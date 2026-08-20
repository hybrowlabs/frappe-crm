<template>
  <div
    class="group flex w-full items-center justify-between rounded bg-transparent p-1 pl-2 text-base text-ink-gray-8 transition-colors hover:bg-surface-gray-3 active:bg-surface-gray-4"
  >
    <div class="flex flex-1 items-center justify-between gap-7">
      <div v-show="!editMode">{{ option.value }}</div>
      <div
        v-show="editMode"
        ref="fieldRef"
        class="w-full"
        @focusout.stop="saveOption"
        @keydown.enter.stop="(e) => e.target.blur()"
      >
        <PhoneInput
          v-if="option.isPhone"
          :value="localOption.value"
          :placeholder="option.placeholder"
          @change="(v) => (localOption.value = v)"
        />
        <TextInput
          v-else
          v-model="localOption.value"
          class="w-full"
          :placeholder="option.placeholder"
        />
      </div>

      <div class="actions flex items-center justify-center">
        <Button
          v-if="editMode"
          variant="ghost"
          :label="__('Save')"
          class="opacity-0 hover:bg-surface-gray-4 group-hover:opacity-100"
          @click="saveOption"
        />
        <Button
          v-if="!isNew && !option.selected"
          :tooltip="__('Set As Primary')"
          variant="ghost"
          :icon="SuccessIcon"
          class="opacity-0 hover:bg-surface-gray-4 group-hover:opacity-100"
          @click="option.onClick"
        />
        <Button
          v-if="!editMode"
          :tooltip="__('Edit')"
          variant="ghost"
          :icon="EditIcon"
          class="opacity-0 hover:bg-surface-gray-4 group-hover:opacity-100"
          @click="toggleEditMode"
        />
        <Button
          :tooltip="__('Delete')"
          variant="ghost"
          icon="x"
          class="opacity-0 hover:bg-surface-gray-4 group-hover:opacity-100"
          @click="() => option.onDelete(option, isNew)"
        />
      </div>
    </div>
    <div v-if="option.selected">
      <FeatherIcon name="check" class="text-ink-gray-5 h-4 w-6" />
    </div>
  </div>
</template>

<script setup>
import SuccessIcon from '@/components/Icons/SuccessIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import PhoneInput from '@/components/Controls/PhoneInput.vue'
import { TextInput } from 'frappe-ui'
import { nextTick, ref, onMounted, reactive, watch } from 'vue'

const props = defineProps({
  option: { type: Object, default: () => {} },
})

const localOption = reactive({ ...props.option })
watch(
  () => props.option,
  (val) => Object.assign(localOption, val),
  { deep: true },
)

const editMode = ref(false)
const isNew = ref(false)
const fieldRef = ref(null)

// the control is a TextInput or a PhoneInput, so reach for the inner input
// rather than a component ref
const focusInput = () =>
  nextTick(() => fieldRef.value?.querySelector('input')?.focus())

onMounted(() => {
  if (!props.option?.value) {
    editMode.value = true
    isNew.value = true
    focusInput()
  }
})

const toggleEditMode = () => {
  editMode.value = !editMode.value
  if (editMode.value) focusInput()
}

const saveOption = () => {
  // focusout and the Save button can both fire for one edit
  if (!editMode.value) return
  if (!localOption.value) return
  toggleEditMode()
  props.option.onSave(
    { ...props.option, value: localOption.value },
    isNew.value,
  )
  isNew.value = false
}
</script>
