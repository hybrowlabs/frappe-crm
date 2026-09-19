// Shared presentational pieces for the role dashboards (CEO, Sales Manager,
// Repeat Business, Technical Pre-Sale, My Dashboard, Marketing).
// Styling lives in src/styles/brand.css (the `pa-*` classes).
import { h } from 'vue'
import LucideArrowRight from '~icons/lucide/arrow-right'
import LucideInbox from '~icons/lucide/inbox'
import LucideSparkles from '~icons/lucide/sparkles'

const toneClass = { green: 'good', red: 'bad', amber: 'warn' }

export const fillClass = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
  purple: 'bg-purple-500',
  gray: 'bg-surface-gray-4',
}

export const SectionLabel = (props) =>
  h('div', { class: 'pa-sec' }, [
    h('h2', props.label),
    props.hint ? h('span', props.hint) : null,
  ])
SectionLabel.props = ['label', 'hint']

// KPI card: coloured icon tile, label, big value, caption; `foot` slot for extras.
export const Tile = (props, { attrs, slots }) =>
  h(
    'div',
    {
      ...attrs,
      class: ['pa-kpi', attrs.onClick && 'link', attrs.class],
      ...(attrs.onClick ? { tabindex: 0, role: 'button' } : {}),
    },
    [
      h('span', { class: 'pa-ico' }, [h(props.icon || LucideSparkles)]),
      h('div', { class: 'pa-body' }, [
        h('div', { class: 'pa-l' }, props.title),
        h('div', { class: ['pa-v', toneClass[props.tone]] }, props.value),
        props.sub ? h('div', { class: 'pa-s' }, props.sub) : null,
        slots.foot?.(),
      ]),
      attrs.onClick ? h(LucideArrowRight, { class: 'pa-go' }) : null,
    ],
  )
Tile.props = ['title', 'value', 'sub', 'tone', 'icon']
Tile.inheritAttrs = false

// Panel with a header strip. `title` slot replaces the title text,
// `right` slot sits at the end of the header, `flush` removes body padding.
export const Card = (props, { attrs, slots }) =>
  h('div', { ...attrs, class: ['pa-panel', attrs.class] }, [
    h('div', { class: 'pa-ph' }, [
      h('div', { class: 'pa-ph-title' }, [
        slots.title ? slots.title() : props.title,
        props.sub ? h('p', props.sub) : null,
      ]),
      slots.right?.(),
    ]),
    h('div', { class: ['pa-pb', props.flush && 'flush'] }, slots.default?.()),
  ])
Card.props = ['title', 'sub', 'flush', 'icon']
Card.inheritAttrs = false

export const Bar = (props) =>
  h('div', { class: 'pa-track' }, [
    h('div', {
      class: ['pa-fill', fillClass[props.color] || fillClass.blue],
      style: `width: ${Math.round(props.ratio * 100)}%`,
    }),
  ])
Bar.props = ['ratio', 'color']

export const BarRow = (props, { attrs }) =>
  h('div', { ...attrs, class: ['pa-bar', attrs.onClick && 'link', attrs.class] }, [
    h('div', { class: 'pa-top' }, [
      h('span', { class: 'pa-name' }, [
        props.rank ? h('span', { class: ['pa-rank', props.rank === 1 && 'r1'] }, props.rank) : null,
        props.label,
      ]),
      h('span', { class: 'pa-num' }, [props.sub ? h('em', props.sub) : null, props.value]),
    ]),
    h(Bar, { ratio: props.ratio, color: props.color }),
  ])
BarRow.props = ['label', 'sub', 'value', 'ratio', 'color', 'rank']
BarRow.inheritAttrs = false

// Wraps BarRows with the mockup's vertical rhythm.
export const Bars = (props, { slots }) => h('div', { class: 'pa-bars' }, slots.default?.())

export const Empty = (props) =>
  h('div', { class: 'pa-empty' }, [
    h('span', [h(props.icon || LucideInbox)]),
    props.text || __('No data'),
  ])
Empty.props = ['text', 'icon']

export const Dot = (props) =>
  h('span', { class: ['pa-dot', fillClass[props.color] || fillClass.gray] })
Dot.props = ['color']
