import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.agents.dataset_profiling_agent.agent.dataset_profiling_agent import (
    DatasetProfilingAgent,
)
from app.db.redis import redis_client

router = APIRouter()


class RunCreateRequest(BaseModel):
    query: str
    domain: str | None = None
    task_type: str | None = None
    dataset_path: str | None = None
    max_iterations: int = 3


async def _run_dataset_profiling(run_id: str, dataset_path: str) -> None:
    """后台任务：跑 DatasetProfilingAgent，把进度和结果写进 Redis。

    agent.run() 是同步阻塞函数（扫数据集 + 算图像质量 + 生成图表），
    会跑几十秒到几分钟，所以用 asyncio.to_thread 包一层，避免阻塞 event loop。
    """
    # 初始状态：运行中
    await redis_client.set(
        f"run:{run_id}",
        json.dumps(
            {
                "run_id": run_id,
                "status": "running",
                "current_node": "dataset_profiling",
                "progress": 0,
                "result": None,
            }
        ),
    )

    try:
        agent = DatasetProfilingAgent()
        # 同步 agent 用 to_thread 丢到线程池跑，不阻塞 async event loop
        result = await asyncio.to_thread(agent.run, {"dataset_path": dataset_path})

        # 跑完了：写最终结果
        await redis_client.set(
            f"run:{run_id}",
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "completed",
                    "current_node": "dataset_profiling",
                    "progress": 100,
                    "result": result,
                }
            ),
        )
    except Exception as e:
        # 失败了：写错误信息
        await redis_client.set(
            f"run:{run_id}",
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "failed",
                    "current_node": "dataset_profiling",
                    "progress": 0,
                    "error": str(e),
                }
            ),
        )


@router.post("")
async def create_run(payload: RunCreateRequest) -> dict[str, str]:
    """创建任务。

    立刻返回 run_id，不等 agent 跑完。
    后台用 asyncio.create_task 启动 agent，状态写进 Redis。
    """
    run_id = f"run_{uuid4().hex[:12]}"

    # 目前只支持 dataset_profiling 这一种任务
    if payload.task_type == "dataset_profiling" and payload.dataset_path:
        asyncio.create_task(_run_dataset_profiling(run_id, payload.dataset_path))
    else:
        # 没匹配的任务类型：直接标记为 created，等后续扩展
        await redis_client.set(
            f"run:{run_id}",
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "created",
                    "current_node": "not_started",
                    "progress": 0,
                    "result": None,
                }
            ),
        )

    return {
        "run_id": run_id,
        "status": "created",
        "query": payload.query,
    }


@router.get("/{run_id}")
async def get_run(run_id: str) -> dict:
    """查询任务状态。

    从 Redis 读 run:{run_id}，返回真实状态 + 最终结果。
    agent 还在跑时 status=running，跑完后 status=completed，失败 status=failed。
    """
    data = await redis_client.get(f"run:{run_id}")
    if not data:
        return {"run_id": run_id, "status": "not_found"}
    return json.loads(data)


# ===========================================================================
# Mock 接口（用于前端闭环演示，等真实 Agent 就绪后可删除）
# ===========================================================================

# ---------- Mock 数据 ----------

_MOCK_PAPER_POOL = [
    {
        "paper_id": "p001",
        "title": "PatchCore: Towards Total Scene Anomaly Detection",
        "authors": ["Karim Roth", "Yongyi Yang"],
        "year": 2022,
        "venue": "CVPR",
        "url": "https://arxiv.org/abs/2106.08265",
        "doi": "10.1109/CVPR52688.2022.01234",
        "arxiv_id": "2106.08265",
        "relevance_score": 0.92,
    },
    {
        "paper_id": "p002",
        "title": "PaDiM: A Patch Distribution Modeling Framework for Anomaly Detection and Localization",
        "authors": ["Victor Lechat", "Guillaume Santer"],
        "year": 2021,
        "venue": "ICPR",
        "url": "https://arxiv.org/abs/2011.08785",
        "doi": "10.1109/ICPR48806.2021.9413",
        "arxiv_id": "2011.08785",
        "relevance_score": 0.88,
    },
    {
        "paper_id": "p003",
        "title": "Deep SVDD for Anomaly Detection on Industrial Images",
        "authors": ["Lukas Ruff", "David Zimmerer"],
        "year": 2018,
        "venue": "ICML",
        "url": "https://arxiv.org/abs/1804.02595",
        "doi": "",
        "arxiv_id": "1804.02595",
        "relevance_score": 0.85,
    },
    {
        "paper_id": "p004",
        "title": "A Unified Model for Anomaly Detection and Few-Shot Classification",
        "authors": ["Yi Liu", "Jia Li"],
        "year": 2023,
        "venue": "ECCV",
        "url": "https://arxiv.org/abs/2303.05288",
        "doi": "",
        "arxiv_id": "2303.05288",
        "relevance_score": 0.81,
    },
    {
        "paper_id": "p005",
        "title": "FastFlow: Unsupervised Anomaly Detection and Localization via 2D Normalizing Flows",
        "authors": ["Jiawei Yu", "Ye Zheng"],
        "year": 2021,
        "venue": "arXiv",
        "url": "https://arxiv.org/abs/2111.07677",
        "doi": "",
        "arxiv_id": "2111.07677",
        "relevance_score": 0.79,
    },
    {
        "paper_id": "p006",
        "title": "Context-Aware Anomaly Detection with Self-Supervised Learning",
        "authors": ["Ming Liu", "Tao Wang"],
        "year": 2024,
        "venue": "AAAI",
        "url": "https://arxiv.org/abs/2401.03145",
        "doi": "",
        "arxiv_id": "2401.03145",
        "relevance_score": 0.76,
    },
    {
        "paper_id": "p007",
        "title": "A Survey on Visual Anomaly Detection",
        "authors": ["Zhihao Chen", "Ruoyu Chen"],
        "year": 2023,
        "venue": "ACM Computing Surveys",
        "url": "https://arxiv.org/abs/2305.16860",
        "doi": "",
        "arxiv_id": "2305.16860",
        "relevance_score": 0.74,
    },
    {
        "paper_id": "p008",
        "title": "Reconstruction-Based Anomaly Detection: A Survey",
        "authors": ["Yan Li", "Xiaogang Xu"],
        "year": 2023,
        "venue": "Pattern Recognition",
        "url": "https://arxiv.org/abs/2302.07429",
        "doi": "",
        "arxiv_id": "2302.07429",
        "relevance_score": 0.72,
    },
    {
        "paper_id": "p009",
        "title": "Scale-Aware Feature Pyramid for Small Defect Detection",
        "authors": ["Han Zhang", "Wei Wei"],
        "year": 2024,
        "venue": "WACV",
        "url": "https://arxiv.org/abs/2309.12345",
        "doi": "",
        "arxiv_id": "2309.12345",
        "relevance_score": 0.70,
    },
    {
        "paper_id": "p010",
        "title": "Multi-Scale Memory Bank for Industrial Anomaly Detection",
        "authors": ["Feng Gao", "Bo Liu"],
        "year": 2024,
        "venue": "ICASSP",
        "url": "https://arxiv.org/abs/2402.04567",
        "doi": "",
        "arxiv_id": "2402.04567",
        "relevance_score": 0.68,
    },
]


_MOCK_FACT_POOL = [
    {
        "fact_id": "f001",
        "claim": "Patch-based reconstruction methods can miss subtle texture anomalies in low-data regimes.",
        "evidence_text": "Patch-based methods struggle with subtle anomalies when training data is limited.",
        "source_paper_id": "p008",
        "section": "Experiments",
        "page": 7,
        "confidence": 0.85,
    },
    {
        "fact_id": "f002",
        "claim": "PatchCore achieves 99.1% image-AUROC on MVTec AD bottle category.",
        "evidence_text": "On MVTec AD, PatchCore achieves 99.1% image-level AUROC and 98.7% pixel-level AUROC on bottle.",
        "source_paper_id": "p001",
        "section": "Results",
        "page": 5,
        "confidence": 0.95,
    },
    {
        "fact_id": "f003",
        "claim": "Small defects occupy less than 5% of image area in MVTec bottle dataset.",
        "evidence_text": "Our analysis shows that 78% of defects in the bottle category occupy less than 5% of the image area.",
        "source_paper_id": "p001",
        "section": "Analysis",
        "page": 8,
        "confidence": 0.82,
    },
    {
        "fact_id": "f004",
        "claim": "PaDiM uses multivariate Gaussian distributions to model normal patch features.",
        "evidence_text": "We model the distribution of normal patch features using a multivariate Gaussian.",
        "source_paper_id": "p002",
        "section": "Method",
        "page": 3,
        "confidence": 0.91,
    },
    {
        "fact_id": "f005",
        "claim": "Deep SVDD requires careful initialization to avoid solution collapse.",
        "evidence_text": "Without proper initialization, Deep SVDD tends to collapse to a trivial solution.",
        "source_paper_id": "p003",
        "section": "Discussion",
        "page": 9,
        "confidence": 0.78,
    },
    {
        "fact_id": "f006",
        "claim": "FastFlow achieves 99.4% image-AUROC on average across MVTec AD categories.",
        "evidence_text": "FastFlow obtains an average image-AUROC of 99.4% on MVTec AD.",
        "source_paper_id": "p005",
        "section": "Results",
        "page": 6,
        "confidence": 0.90,
    },
    {
        "fact_id": "f007",
        "claim": "Self-supervised pretraining improves anomaly detection performance by 3-5% on industrial datasets.",
        "evidence_text": "Our experiments show that self-supervised pretraining yields 3-5% improvement in AUROC.",
        "source_paper_id": "p006",
        "section": "Experiments",
        "page": 5,
        "confidence": 0.84,
    },
    {
        "fact_id": "f008",
        "claim": "Scale-aware feature pyramids improve small defect localization by 8% pixel-AUROC.",
        "evidence_text": "Our scale-aware design improves pixel-AUROC by 8% on small defect categories.",
        "source_paper_id": "p009",
        "section": "Results",
        "page": 7,
        "confidence": 0.87,
    },
    {
        "fact_id": "f009",
        "claim": "Memory-based methods scale poorly with dataset size due to O(N) retrieval cost.",
        "evidence_text": "Memory bank retrieval scales linearly with the number of stored features.",
        "source_paper_id": "p010",
        "section": "Discussion",
        "page": 8,
        "confidence": 0.76,
    },
    {
        "fact_id": "f010",
        "claim": "Reconstruction-based methods tend to over-generalize and fail to flag subtle anomalies.",
        "evidence_text": "Reconstruction models can over-generalize and reconstruct anomalous regions.",
        "source_paper_id": "p008",
        "section": "Limitations",
        "page": 10,
        "confidence": 0.83,
    },
    {
        "fact_id": "f011",
        "claim": "Texture categories show higher intra-class variation than object categories in MVTec AD.",
        "evidence_text": "Texture categories like carpet and leather show 2.3x higher intra-class variation.",
        "source_paper_id": "p007",
        "section": "Analysis",
        "page": 12,
        "confidence": 0.80,
    },
    {
        "fact_id": "f012",
        "claim": "Few-shot anomaly detection remains an open problem with no dominant approach.",
        "evidence_text": "Despite recent progress, few-shot anomaly detection has no clear winner.",
        "source_paper_id": "p007",
        "section": "Open Problems",
        "page": 15,
        "confidence": 0.88,
    },
    {
        "fact_id": "f013",
        "claim": "PRO metric is more sensitive to small defects than pixel-AUROC.",
        "evidence_text": "PRO gives more weight to small connected components, making it sensitive to small defects.",
        "source_paper_id": "p001",
        "section": "Metrics",
        "page": 4,
        "confidence": 0.86,
    },
    {
        "fact_id": "f014",
        "claim": "Data augmentation with CutPaste improves anomaly detection on texture categories.",
        "evidence_text": "CutPaste augmentation yields 2.1% improvement on texture categories.",
        "source_paper_id": "p004",
        "section": "Experiments",
        "page": 6,
        "confidence": 0.79,
    },
    {
        "fact_id": "f015",
        "claim": "Multi-scale features capture anomalies at different granularity levels.",
        "evidence_text": "Combining features from layers 2-4 captures anomalies at multiple scales.",
        "source_paper_id": "p002",
        "section": "Method",
        "page": 3,
        "confidence": 0.85,
    },
    {
        "fact_id": "f016",
        "claim": "Industrial anomaly detection datasets are often highly imbalanced.",
        "evidence_text": "Industrial datasets typically have less than 10% anomalous samples.",
        "source_paper_id": "p007",
        "section": "Datasets",
        "page": 5,
        "confidence": 0.92,
    },
    {
        "fact_id": "f017",
        "claim": "Normalizing flows can model complex distributions but require careful architecture choice.",
        "evidence_text": "2D normalizing flows are sensitive to the choice of coupling layers.",
        "source_paper_id": "p005",
        "section": "Discussion",
        "page": 7,
        "confidence": 0.77,
    },
    {
        "fact_id": "f018",
        "claim": "Knowledge distillation from pretrained models improves small dataset performance.",
        "evidence_text": "Distillation from ImageNet-pretrained models yields 4.2% AUROC improvement.",
        "source_paper_id": "p004",
        "section": "Results",
        "page": 8,
        "confidence": 0.83,
    },
    {
        "fact_id": "f019",
        "claim": "Per-region aggregation of anomaly scores improves localization accuracy.",
        "evidence_text": "Region-based aggregation outperforms pixel-wise aggregation by 3.5% pixel-AUROC.",
        "source_paper_id": "p009",
        "section": "Method",
        "page": 4,
        "confidence": 0.81,
    },
    {
        "fact_id": "f020",
        "claim": "Anomaly detection models often fail to generalize across different defect types.",
        "evidence_text": "Models trained on one defect type show 15-20% performance drop on unseen defect types.",
        "source_paper_id": "p007",
        "section": "Limitations",
        "page": 14,
        "confidence": 0.84,
    },
]


_MOCK_GAP_POOL = [
    {
        "gap_id": "g001",
        "description": "现有方法未充分研究小缺陷定位的尺度先验问题",
        "supporting_facts": ["f003", "f008"],
        "source_papers": ["p001", "p009"],
        "gap_type": "methodology",
    },
    {
        "gap_id": "g002",
        "description": "少样本工业异常检测缺乏统一的基准和方法对比",
        "supporting_facts": ["f012", "f016"],
        "source_papers": ["p007", "p004"],
        "gap_type": "evaluation",
    },
    {
        "gap_id": "g003",
        "description": "重建类方法在细微纹理异常上容易过度泛化",
        "supporting_facts": ["f001", "f010", "f011"],
        "source_papers": ["p008", "p007"],
        "gap_type": "methodology",
    },
]


_MOCK_HYPOTHESIS_POOL = [
    {
        "hypothesis_id": "h001",
        "source_agent": "data_driven",
        "hypothesis": "在少样本工业异常检测中，显式建模缺陷面积比例作为尺度先验，能提升小缺陷定位稳定性",
        "mechanism": "小缺陷被全局重建损失稀释，尺度感知先验能增加对局部残差的敏感度",
        "expected_effect": "提升 pixel-AUROC 和 PRO 指标",
        "required_data": ["normal images", "limited defect masks"],
        "test_method": "PatchCore 基线 + 尺度感知残差加权模块对比",
        "supporting_evidence": ["f003", "f008"],
        "risks": ["可能在特定缺陷类别上过拟合"],
        "scores": {"novelty": 75, "feasibility": 80, "evidence": 70, "reproducibility": 75},
    },
    {
        "hypothesis_id": "h002",
        "source_agent": "gap_driven",
        "hypothesis": "基于多尺度记忆库的异常检测方法能同时处理大缺陷和小缺陷",
        "mechanism": "不同尺度的特征记忆库能捕获不同大小的异常区域",
        "expected_effect": "在 MVTec AD 全类别上提升 2-3% 平均 AUROC",
        "required_data": ["normal images", "pretrained backbone"],
        "test_method": "对比单尺度 vs 多尺度记忆库",
        "supporting_evidence": ["f009", "f015"],
        "risks": ["多尺度特征会增加计算开销"],
        "scores": {"novelty": 70, "feasibility": 78, "evidence": 72, "reproducibility": 80},
    },
    {
        "hypothesis_id": "h003",
        "source_agent": "literature_driven",
        "hypothesis": "自监督预训练结合 CutPaste 数据增强能改善纹理类异常检测",
        "mechanism": "CutPaste 强制模型学习局部纹理模式，自监督预训练提供更好的特征初始化",
        "expected_effect": "在 carpet/leather 等纹理类别上提升 3-5% AUROC",
        "required_data": ["normal images", "self-supervised pretext task"],
        "test_method": "对比有/无 CutPaste + 自监督预训练",
        "supporting_evidence": ["f014", "f007", "f011"],
        "risks": ["预训练成本高，CutPaste 超参敏感"],
        "scores": {"novelty": 65, "feasibility": 75, "evidence": 80, "reproducibility": 78},
    },
    {
        "hypothesis_id": "h004",
        "source_agent": "data_driven",
        "hypothesis": "区域级异常分数聚合比像素级聚合更适合小缺陷定位",
        "mechanism": "区域聚合能减少噪声像素的影响，突出真实异常区域",
        "expected_effect": "pixel-AUROC 提升 3.5%，PRO 提升 5%",
        "required_data": ["normal images", "defect masks"],
        "test_method": "对比像素级 vs 区域级聚合策略",
        "supporting_evidence": ["f019", "f013"],
        "risks": ["区域划分策略需要手动设计"],
        "scores": {"novelty": 68, "feasibility": 82, "evidence": 75, "reproducibility": 85},
    },
    {
        "hypothesis_id": "h005",
        "source_agent": "gap_driven",
        "hypothesis": "知识蒸馏能缓解工业异常检测中小数据集的性能下降",
        "mechanism": "从 ImageNet 预训练模型蒸馏知识，提供更鲁棒的特征表示",
        "expected_effect": "在仅有 10% 训练数据时提升 4.2% AUROC",
        "required_data": ["normal images", "pretrained teacher model"],
        "test_method": "对比有/无知识蒸馏的性能差异",
        "supporting_evidence": ["f018"],
        "risks": ["蒸馏温度和比例需要调优"],
        "scores": {"novelty": 60, "feasibility": 85, "evidence": 78, "reproducibility": 82},
    },
    {
        "hypothesis_id": "h006",
        "source_agent": "literature_driven",
        "hypothesis": "条件归一化流能更好地建模正常分布的复杂结构",
        "mechanism": "条件归一化流能根据输入类别调整分布参数，适应不同类别",
        "expected_effect": "在类别差异大的数据集上提升 2-4% AUROC",
        "required_data": ["normal images", "category labels"],
        "test_method": "对比标准归一化流 vs 条件归一化流",
        "supporting_evidence": ["f017"],
        "risks": ["训练不稳定，需要大量数据"],
        "scores": {"novelty": 78, "feasibility": 65, "evidence": 60, "reproducibility": 70},
    },
]


_MOCK_REVIEW_POOL = []
_REVIEWER_TYPES = ["novelty", "feasibility", "evidence", "reproducibility"]
_REVIEW_REASONS = {
    "novelty": "评估创新性：与已有工作的差异程度",
    "feasibility": "评估可行性：在比赛时间和算力内的可验证性",
    "evidence": "评估证据强度：是否有充分论文和数据支撑",
    "reproducibility": "评估可复现性：实验设置是否明确可复现",
}
for _h in _MOCK_HYPOTHESIS_POOL:
    for _rt in _REVIEWER_TYPES:
        _MOCK_REVIEW_POOL.append({
            "review_id": f"r_{_h['hypothesis_id']}_{_rt}",
            "hypothesis_id": _h["hypothesis_id"],
            "reviewer_type": _rt,
            "score": _h["scores"][_rt],
            "reason": _REVIEW_REASONS[_rt],
            "suggestion": "详见假设详情，建议关注低分项",
        })


_MOCK_POOLS = {
    "paper": _MOCK_PAPER_POOL,
    "fact": _MOCK_FACT_POOL,
    "gap": _MOCK_GAP_POOL,
    "hypothesis": _MOCK_HYPOTHESIS_POOL,
    "review": _MOCK_REVIEW_POOL,
}


_MOCK_ARTIFACTS = [
    {"type": "dataset_plot", "path": "outputs/runs/run_mock_001/class_distribution.png", "description": "类别分布图"},
    {"type": "dataset_plot", "path": "outputs/runs/run_mock_001/quality_distribution.png", "description": "图像质量分布"},
    {"type": "dataset_plot", "path": "outputs/runs/run_mock_001/split_comparison.png", "description": "划分对比图"},
    {"type": "experiment_plot", "path": "outputs/runs/run_mock_001/auroc_curve.png", "description": "AUROC 曲线"},
    {"type": "experiment_plot", "path": "outputs/runs/run_mock_001/ablation_chart.png", "description": "消融实验图"},
    {"type": "final_report", "path": "outputs/runs/run_mock_001/final_report.md", "description": "最终报告"},
]


_MOCK_FINAL_REPORT = {
    "problem_statement": "工业缺陷检测中，小缺陷定位不稳定是当前主流方法的核心瓶颈。在 MVTec AD 数据集上，约 78% 的缺陷占用面积小于 5%，现有方法在这些小缺陷上的 pixel-AUROC 普遍比大缺陷低 8-12%。",
    "rationale": "基于对 10 篇相关论文的调研和 20 条带来源证据的整理，我们发现：（1）小缺陷被全局重建损失稀释；（2）尺度感知先验能增加对局部残差的敏感度；（3）区域级聚合能减少噪声像素影响。因此提出尺度感知的异常检测方法。",
    "technical_details": "在 PatchCore 基线上添加尺度感知残差加权模块：1) 多尺度特征提取（layer2-4）；2) 尺度感知权重预测网络；3) 区域级异常分数聚合。",
    "datasets": {
        "name": "MVTec AD",
        "splits": {"train": "正常样本", "test": "正常+异常样本"},
        "categories": ["bottle", "cable", "carpet", "grid", "pill"],
    },
    "source": {
        "url": "https://www.mvtec.com/company/research/datasets/mvtec-ad",
        "version": "MVTec AD 2019",
    },
    "paper_title": "Scale-Aware PatchCore: Improving Small Defect Localization in Industrial Anomaly Detection",
    "paper_abstract": "We propose Scale-Aware PatchCore, an extension of PatchCore that explicitly models defect area ratio as a scale prior. Our method introduces a scale-aware residual weighting module and region-level anomaly score aggregation. Experiments on MVTec AD show 4.2% improvement in pixel-AUROC and 6.1% improvement in PRO on small defect categories.",
    "methods": "1) 使用 ResNet-50 提取多尺度特征；2) 训练尺度感知权重预测网络；3) 区域级聚合异常分数；4) 与 PatchCore 基线对比。",
    "experiments": {
        "baseline": "PatchCore",
        "metrics": ["image-AUROC", "pixel-AUROC", "PRO", "F1"],
        "ablation": ["w/o scale-aware", "w/o region aggregation", "w/o multi-scale"],
    },
    "results": {
        "image_auroc": {"baseline": 99.1, "ours": 99.4},
        "pixel_auroc": {"baseline": 98.3, "ours": 98.9},
        "pro": {"baseline": 92.5, "ours": 94.8},
        "small_defect_pixel_auroc": {"baseline": 89.2, "ours": 93.4},
    },
    "references": [
        {"paper_id": "p001", "title": "PatchCore: Towards Total Scene Anomaly Detection"},
        {"paper_id": "p009", "title": "Scale-Aware Feature Pyramid for Small Defect Detection"},
        {"paper_id": "p002", "title": "PaDiM: A Patch Distribution Modeling Framework"},
        {"paper_id": "p007", "title": "A Survey on Visual Anomaly Detection"},
        {"paper_id": "p008", "title": "Reconstruction-Based Anomaly Detection: A Survey"},
    ],
}


# 模块级状态：保存人工选中的假设（POST /feedback 时更新）
_MOCK_SELECTED_HYPOTHESIS: dict = {}


class FeedbackRequest(BaseModel):
    decision: str  # "approve" | "reject"
    selected_hypothesis_id: str | None = None
    comments: str | None = None


@router.get("/{run_id}/results")
async def get_results(
    run_id: str,
    pool_type: str = Query(..., regex="^(paper|fact|gap|hypothesis|review)$"),
):
    """查询某个 Pool 的内容（mock 版）。

    前端调用：GET /runs/run_xxx/results?pool_type=hypothesis
    """
    items = _MOCK_POOLS[pool_type]
    return {
        "run_id": run_id,
        "pool_type": pool_type,
        "count": len(items),
        "items": items,
    }


@router.post("/{run_id}/feedback")
async def post_feedback(run_id: str, payload: FeedbackRequest):
    """人工选择/驳回假设（mock 版）。

    decision="approve" 时记录选中的假设；
    decision="reject" 时清空选中状态。
    """
    if payload.decision == "approve" and payload.selected_hypothesis_id:
        selected = next(
            (h for h in _MOCK_HYPOTHESIS_POOL
             if h["hypothesis_id"] == payload.selected_hypothesis_id),
            None,
        )
        if selected:
            _MOCK_SELECTED_HYPOTHESIS.clear()
            _MOCK_SELECTED_HYPOTHESIS.update(selected)
        return {
            "run_id": run_id,
            "status": "approved",
            "selected_hypothesis_id": payload.selected_hypothesis_id,
            "selected": selected,
            "comments": payload.comments,
        }
    else:
        _MOCK_SELECTED_HYPOTHESIS.clear()
        return {
            "run_id": run_id,
            "status": "rejected",
            "comments": payload.comments,
        }


@router.get("/{run_id}/artifacts")
async def get_artifacts(run_id: str):
    """获取产物列表（mock 版）。"""
    return {"run_id": run_id, "artifacts": _MOCK_ARTIFACTS}


@router.get("/{run_id}/report")
async def get_report(run_id: str):
    """获取最终报告（mock 版）。"""
    return {
        "run_id": run_id,
        "report": _MOCK_FINAL_REPORT,
        "selected_hypothesis": _MOCK_SELECTED_HYPOTHESIS,
    }


# ---------- Tool Execution 日志 mock 数据 ----------

_MOCK_TOOL_CALLS = [
    {
        "call_id": "tc_001",
        "tool_name": "dataset_scan",
        "input": {"dataset_path": "app/agents/dataset_profiling_agent/demo_dataset/MVTec/bottle"},
        "output_summary": "扫描到 287 张图像，2 个划分（train/test），1 个类别",
        "status": "success",
        "error": None,
        "duration_sec": 0.42,
        "timestamp": "2026-07-19T10:00:01Z",
    },
    {
        "call_id": "tc_002",
        "tool_name": "annotation_parser",
        "input": {"annotation_path": "ground_truth/broken_large/000_mask.png"},
        "output_summary": "解析 COCO 格式标注，5 个类别，250 个 bbox",
        "status": "success",
        "error": None,
        "duration_sec": 1.15,
        "timestamp": "2026-07-19T10:00:02Z",
    },
    {
        "call_id": "tc_003",
        "tool_name": "image_quality",
        "input": {"dataset_path": "app/agents/dataset_profiling_agent/demo_dataset/MVTec/bottle"},
        "output_summary": "计算 287 张图像的质量指标（模糊/亮度/对比度）",
        "status": "success",
        "error": None,
        "duration_sec": 3.28,
        "timestamp": "2026-07-19T10:00:05Z",
    },
    {
        "call_id": "tc_004",
        "tool_name": "opencv_image_analyzer",
        "input": {"dataset_path": "app/agents/dataset_profiling_agent/demo_dataset/MVTec/bottle"},
        "output_summary": "OpenCV 分析：尺寸分布、缺陷比例、分布差异",
        "status": "success",
        "error": None,
        "duration_sec": 2.05,
        "timestamp": "2026-07-19T10:00:08Z",
    },
    {
        "call_id": "tc_005",
        "tool_name": "plot_generator",
        "input": {"scan": "...", "quality": "...", "analysis": "..."},
        "output_summary": "生成 4 张 Plotly 交互图 + 6 张样本图",
        "status": "success",
        "error": None,
        "duration_sec": 0.87,
        "timestamp": "2026-07-19T10:00:09Z",
    },
]


@router.get("/{run_id}/tool_calls")
async def get_tool_calls(run_id: str):
    """获取工具执行日志（mock 版）。

    对应 DC-15：展示工具调用 input、output、status、error。
    """
    return {"run_id": run_id, "tool_calls": _MOCK_TOOL_CALLS}
