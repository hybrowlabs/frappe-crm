<template>
  <StageFormDialog
    v-model="show"
    :title="__('New Deal')"
    :subtitle="subtitle"
    size="2xl"
  >
    <StageCallout theme="blue" icon="zap" class="mb-3">
      {{ __('Confirm this is') }} <b>{{ __('new business') }}</b>
      {{
        __(
          '— not a reorder. Capture the trigger to start the deal at Requirements Discussion.',
        )
      }}
    </StageCallout>

    <StageSection :title="__('Why are you converting?')" icon="zap">
      <FieldRadioGroup
        v-model="why"
        :options="whyOptions"
        :error="errors.why"
      />
    </StageSection>

    <StageSection :title="__('Timeline')" icon="clock">
      <FieldSelect
        v-model="timeline"
        :label="__('Close Timeline')"
        required
        :options="timelineOptions"
        :placeholder="__('Select timeline')"
        :error="errors.timeline"
      />
    </StageSection>

    <StageSection :title="__('Contact')" icon="users">
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <FieldText
          v-model="firstName"
          :label="__('First Name')"
          required
          :error="errors.firstName"
        />
        <FieldText v-model="lastName" :label="__('Last Name')" />
        <FieldText
          v-model="email"
          :label="__('Email')"
          type="email"
          :error="errors.email"
        />
        <FieldText
          v-model="mobileNo"
          :label="__('Mobile No.')"
          :error="errors.mobileNo"
        />
      </div>
    </StageSection>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Create & Open Deal')"
          :loading="creating"
          @click="createDeal"
        >
          <template #suffix><StageIcon name="arrowRight" class="h-4 w-4" /></template>
        </Button>
      </div>
    </template>
  </StageFormDialog>
</template>

<script setup>
import StageFormDialog from '@/components/StageForms/StageFormDialog.vue'
import StageSection from '@/components/StageForms/StageSection.vue'
import StageCallout from '@/components/StageForms/StageCallout.vue'
import StageIcon from '@/components/StageForms/StageIcon.vue'
import FieldSelect from '@/components/StageForms/FieldSelect.vue'
import FieldRadioGroup from '@/components/StageForms/FieldRadioGroup.vue'
import FieldText from '@/components/StageForms/FieldText.vue'
import { usersStore } from '@/stores/users'
import { Button, createResource, toast } from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  org: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const router = useRouter()
const { getUser } = usersStore()

const whyOptions = [
  __('New product or application — first time enquiry'),
  __('Existing customer wants to try a different product'),
  __('Problem identified — needs technical recommendation'),
  __('Trial requested by customer'),
]
const timelineOptions = [
  'Immediate (<1 month)',
  'Short (<2 months)',
  'Medium (3-6 months)',
]

// ---- form state ----
const territory = ref('')
createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'CRM Organization',
    filters: props.org,
    fieldname: 'territory',
  },
  auto: true,
  onSuccess: (d) => (territory.value = d?.territory || ''),
})

const why = ref('')
const timeline = ref('')
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const mobileNo = ref('')
const creating = ref(false)

const attempted = ref(false)
const fieldValues = { why, timeline, firstName }
const errors = computed(() => {
  if (!attempted.value) return {}
  const e = {}
  for (const k of Object.keys(fieldValues)) {
    if (!fieldValues[k].value) e[k] = __('Required')
  }
  if (email.value && !email.value.includes('@')) {
    e.email = __('Invalid email address')
  }
  if (mobileNo.value && isNaN(mobileNo.value.replace(/[-+() ]/g, ''))) {
    e.mobileNo = __('Mobile No. should be a number')
  }
  return e
})

function createDeal() {
  attempted.value = true
  if (Object.keys(errors.value).length) return
  creating.value = true
  createResource({
    url: 'crm.fcrm.doctype.crm_deal.crm_deal.create_deal',
    params: {
      doc: {
        organization: props.org,
        territory: territory.value,
        status: 'Req. Discussion',
        deal_owner: getUser().name,
        conversion_reason: why.value,
        close_timeline: timeline.value,
        first_name: firstName.value,
        last_name: lastName.value,
        email: email.value,
        mobile_no: mobileNo.value,
      },
    },
    auto: true,
    onSuccess(name) {
      creating.value = false
      show.value = false
      router.push({ name: 'Deal', params: { dealId: name } })
    },
    onError(err) {
      creating.value = false
      toast.error(err.messages?.[0] || __('Error creating deal'))
    },
  })
}
</script>
