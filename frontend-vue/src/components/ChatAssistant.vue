<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { ChatDotRound, Close, Delete, Promotion } from '@element-plus/icons-vue'
import { sendChat } from '../api/runs'
import { shortRunId } from '../utils/format'

const props = defineProps({
  runId: { type: String, default: '' },
})

const open = ref(false)
const input = ref('')
const sending = ref(false)
const error = ref('')
const messages = ref([])
const messageList = ref(null)
const modelName = ref('')

const conversationId = computed(() => props.runId || 'general')
const storageKey = computed(() => `cv-scientist-chat:${conversationId.value}`)
const contextLabel = computed(() => props.runId ? shortRunId(props.runId) : '通用研究')
const welcomeText = computed(() =>
  props.runId
    ? '已关联当前任务。你想先分析数据画像、标注质量，还是实验方向？'
    : '你好。可以从一个计算机视觉研究问题开始。',
)

function loadConversation() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey.value) || '[]')
    messages.value = Array.isArray(saved) ? saved : []
  } catch {
    messages.value = []
  }
  error.value = ''
}

function persistConversation() {
  sessionStorage.setItem(storageKey.value, JSON.stringify(messages.value.slice(-30)))
}

async function scrollToBottom() {
  await nextTick()
  if (messageList.value) {
    messageList.value.scrollTop = messageList.value.scrollHeight
  }
}

async function submit() {
  const content = input.value.trim()
  if (!content || sending.value) return

  messages.value.push({ role: 'user', content })
  input.value = ''
  error.value = ''
  persistConversation()
  sending.value = true
  await scrollToBottom()

  try {
    const data = await sendChat({
      run_id: props.runId || null,
      messages: messages.value.slice(-12).map(({ role, content: text }) => ({ role, content: text })),
    })
    messages.value.push({ role: 'assistant', content: data.answer })
    modelName.value = data.model || ''
    persistConversation()
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

function clearConversation() {
  messages.value = []
  error.value = ''
  sessionStorage.removeItem(storageKey.value)
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}

watch(conversationId, loadConversation, { immediate: true })
watch(open, (value) => {
  if (value) scrollToBottom()
})
</script>

<template>
  <div class="chat-assistant">
    <transition name="chat-panel">
      <section v-if="open" class="chat-panel" aria-label="研究助手对话">
        <header class="chat-header">
          <div class="assistant-identity">
            <span class="assistant-mark"><el-icon><ChatDotRound /></el-icon></span>
            <div>
              <strong>研究助手</strong>
              <small><i />{{ contextLabel }}</small>
            </div>
          </div>
          <div class="chat-tools">
            <el-tooltip content="清空当前会话" placement="bottom">
              <el-button :icon="Delete" text circle aria-label="清空当前会话" :disabled="!messages.length" @click="clearConversation" />
            </el-tooltip>
            <el-button :icon="Close" text circle aria-label="关闭研究助手" @click="open = false" />
          </div>
        </header>

        <div ref="messageList" class="message-list" aria-live="polite">
          <div v-if="!messages.length" class="welcome-message">
            <span class="assistant-mark compact"><el-icon><ChatDotRound /></el-icon></span>
            <p>{{ welcomeText }}</p>
          </div>

          <div v-for="(message, index) in messages" :key="index" class="message-row" :class="message.role">
            <div class="message-bubble">{{ message.content }}</div>
          </div>

          <div v-if="sending" class="message-row assistant">
            <div class="message-bubble thinking" aria-label="正在生成回答"><i /><i /><i /></div>
          </div>
        </div>

        <div v-if="error" class="chat-error">{{ error }}</div>

        <footer class="chat-composer">
          <el-input
            v-model="input"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 4 }"
            maxlength="4000"
            resize="none"
            placeholder="输入问题，Enter 发送"
            aria-label="对话输入"
            @keydown="handleKeydown"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            circle
            :loading="sending"
            :disabled="!input.trim()"
            aria-label="发送消息"
            @click="submit"
          />
        </footer>
        <div class="chat-footnote">{{ modelName || 'Qwen' }} · 回答基于当前可用上下文</div>
      </section>
    </transition>

    <el-tooltip content="研究助手" placement="left">
      <el-button
        v-if="!open"
        class="chat-trigger"
        type="primary"
        :icon="ChatDotRound"
        circle
        aria-label="打开研究助手"
        @click="open = true"
      />
    </el-tooltip>
  </div>
</template>

<style scoped>
.chat-assistant {
  position: fixed;
  z-index: 75;
  right: 0;
  bottom: 0;
  width: 0;
  height: 0;
}
.chat-trigger {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 46px;
  height: 46px;
  box-shadow: 0 12px 30px rgba(20, 33, 36, .22);
}
.chat-panel {
  position: fixed;
  right: 24px;
  bottom: 24px;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto auto auto;
  width: min(400px, calc(100vw - 32px));
  height: min(640px, calc(100vh - 48px));
  overflow: hidden;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: 0 24px 70px rgba(20, 33, 36, .2);
}
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 64px;
  padding: 0 14px;
  border-bottom: 1px solid var(--line);
}
.assistant-identity { display: flex; align-items: center; gap: 10px; min-width: 0; }
.assistant-mark {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: var(--brand);
  color: #fff;
}
.assistant-mark.compact { width: 28px; height: 28px; border-radius: 7px; font-size: 13px; }
.assistant-identity > div { display: grid; gap: 3px; min-width: 0; }
.assistant-identity strong { color: var(--text); font-size: 14px; }
.assistant-identity small { display: flex; align-items: center; gap: 5px; color: var(--text-muted); font-family: Consolas, monospace; font-size: 10px; }
.assistant-identity small i { width: 5px; height: 5px; border-radius: 50%; background: var(--success); }
.chat-tools { display: flex; }
.message-list { min-height: 0; overflow-y: auto; padding: 16px; background: var(--surface-raised); }
.welcome-message { display: flex; align-items: flex-start; gap: 10px; padding: 12px; border-bottom: 1px solid var(--line); }
.welcome-message p { margin: 2px 0 0; color: var(--text-secondary); font-size: 13px; line-height: 1.65; }
.message-row { display: flex; margin-top: 13px; }
.message-row.user { justify-content: flex-end; }
.message-bubble {
  max-width: 86%;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.65;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}
.message-row.user .message-bubble { border-color: var(--brand); background: var(--brand); color: #fff; }
.thinking { display: flex; align-items: center; gap: 4px; min-width: 50px; min-height: 38px; }
.thinking i { width: 5px; height: 5px; border-radius: 50%; background: var(--text-muted); animation: chat-thinking 1s infinite ease-in-out; }
.thinking i:nth-child(2) { animation-delay: .12s; }
.thinking i:nth-child(3) { animation-delay: .24s; }
.chat-error { padding: 8px 14px; border-top: 1px solid #fecaca; background: #fef2f2; color: var(--danger); font-size: 11px; line-height: 1.45; }
.chat-composer { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: 8px; padding: 12px 12px 8px; border-top: 1px solid var(--line); }
.chat-composer :deep(.el-textarea__inner) { min-height: 40px !important; max-height: 108px; padding: 10px 12px; }
.chat-composer .el-button { width: 40px; height: 40px; }
.chat-footnote { padding: 0 14px 10px; color: var(--text-muted); font-size: 10px; text-align: center; }
.chat-panel-enter-active, .chat-panel-leave-active { transition: opacity .18s ease, transform .18s ease; }
.chat-panel-enter-from, .chat-panel-leave-to { opacity: 0; transform: translateY(8px) scale(.98); }

@keyframes chat-thinking {
  0%, 60%, 100% { opacity: .35; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-2px); }
}

@media (max-width: 600px) {
  .chat-trigger { right: 16px; bottom: 18px; }
  .chat-panel {
    top: 56px;
    right: 0;
    bottom: 0;
    left: 0;
    width: 100%;
    height: auto;
    border-right: 0;
    border-bottom: 0;
    border-left: 0;
    border-radius: 0;
  }
}
</style>
