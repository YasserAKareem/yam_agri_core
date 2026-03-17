# YAM Server UI Kit - Repository Creation Guide

> **Repository:** `yam-server-ui-kit`
> **Purpose:** Vue 3 UI/UX design system based on frappe-ui with reusable components
> **Owner:** UI/UX Designers, Frontend Engineers
> **Release Cadence:** Frequent - iterative design improvements

---

## GitHub Repository Form

### Repository Name
```
yam-server-ui-kit
```

### Description
```
Vue 3 UI design system for YAM Server based on frappe-ui. Reusable components, design tokens, accessibility patterns. Build once, use everywhere.
```

### Topics
```
vue3, design-system, frappe-ui, component-library, design-tokens,
accessibility, ui-kit, yam-server, storybook
```

---

## File Structure

```
yam-server-ui-kit/
├── src/
│   ├── components/
│   │   ├── base/
│   │   │   ├── Button/
│   │   │   │   ├── Button.vue
│   │   │   │   ├── Button.stories.ts
│   │   │   │   └── Button.spec.ts
│   │   │   ├── Input/
│   │   │   ├── Card/
│   │   │   └── Badge/
│   │   ├── ai/
│   │   │   ├── AIAssistCard/
│   │   │   ├── ConfidenceIndicator/
│   │   │   ├── SuggestionPanel/
│   │   │   └── ModelSelector/
│   │   ├── data/
│   │   │   ├── DataTable/
│   │   │   ├── SearchBar/
│   │   │   └── Pagination/
│   │   └── layouts/
│   │       ├── AppLayout/
│   │       ├── DashboardLayout/
│   │       └── FormLayout/
│   ├── tokens/
│   │   ├── colors.ts
│   │   ├── typography.ts
│   │   ├── spacing.ts
│   │   ├── shadows.ts
│   │   └── breakpoints.ts
│   ├── composables/
│   │   ├── useTheme.ts
│   │   ├── useBreakpoint.ts
│   │   └── useAccessibility.ts
│   ├── utils/
│   │   ├── cn.ts  # Class name merging
│   │   └── a11y.ts  # Accessibility helpers
│   └── styles/
│       ├── base.css
│       ├── utilities.css
│       └── themes/
│           ├── light.css
│           └── dark.css
├── .storybook/
│   ├── main.ts
│   ├── preview.ts
│   └── theme.ts
├── docs/
│   ├── design-principles.md
│   ├── accessibility.md
│   ├── theming.md
│   └── contributing.md
├── examples/
│   ├── dashboard/
│   ├── form/
│   └── data-table/
└── package.json
```

---

## Design Tokens

```typescript
// src/tokens/colors.ts
export const colors = {
  // Primary (YAM Brand)
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',  // Primary
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },

  // Semantic
  success: { /* ... */ },
  warning: { /* ... */ },
  danger: { /* ... */ },
  info: { /* ... */ },

  // Neutral (Grayscale)
  gray: { /* ... */ },

  // AI Indicators
  ai: {
    confidence: {
      high: '#10b981',      // Green
      medium: '#f59e0b',    // Amber
      low: '#ef4444',       // Red
    },
    suggestion: '#8b5cf6',  // Purple
    processing: '#06b6d4',  // Cyan
  }
}

// src/tokens/typography.ts
export const typography = {
  fontFamily: {
    sans: 'Inter, system-ui, sans-serif',
    mono: 'JetBrains Mono, monospace',
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem',// 30px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  }
}
```

---

## Key Components

### AIAssistCard

```vue
<!-- src/components/ai/AIAssistCard/AIAssistCard.vue -->
<template>
  <Card class="ai-assist-card border-l-4" :class="borderColor">
    <div class="flex items-start gap-3">
      <!-- AI Icon -->
      <div class="flex-shrink-0">
        <SparklesIcon class="h-5 w-5" :class="iconColor" />
      </div>

      <!-- Content -->
      <div class="flex-1">
        <!-- Header -->
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-medium text-gray-900">
            {{ title }}
          </h3>
          <ConfidenceIndicator :score="confidence" />
        </div>

        <!-- Suggestion Text -->
        <div class="text-sm text-gray-600 mb-3">
          {{ suggestion }}
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            @click="$emit('accept')"
          >
            Accept
          </Button>
          <Button
            variant="secondary"
            size="sm"
            @click="$emit('edit')"
          >
            Edit
          </Button>
          <Button
            variant="ghost"
            size="sm"
            @click="$emit('dismiss')"
          >
            Dismiss
          </Button>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Card, Button } from '../base'
import { ConfidenceIndicator } from './'
import { SparklesIcon } from '@heroicons/vue/24/outline'

interface Props {
  title: string
  suggestion: string
  confidence: number  // 0-100
}

const props = defineProps<Props>()

defineEmits<{
  accept: []
  edit: []
  dismiss: []
}>()

const borderColor = computed(() => {
  if (props.confidence >= 80) return 'border-ai-confidence-high'
  if (props.confidence >= 50) return 'border-ai-confidence-medium'
  return 'border-ai-confidence-low'
})

const iconColor = computed(() => {
  if (props.confidence >= 80) return 'text-ai-confidence-high'
  if (props.confidence >= 50) return 'text-ai-confidence-medium'
  return 'text-ai-confidence-low'
})
</script>
```

### ConfidenceIndicator

```vue
<!-- src/components/ai/ConfidenceIndicator/ConfidenceIndicator.vue -->
<template>
  <div class="flex items-center gap-1.5">
    <!-- Icon -->
    <component :is="icon" class="h-4 w-4" :class="color" />

    <!-- Label -->
    <span class="text-xs font-medium" :class="color">
      {{ label }}
    </span>

    <!-- Percentage (optional) -->
    <span v-if="showPercentage" class="text-xs text-gray-500">
      ({{ confidence }}%)
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon
} from '@heroicons/vue/24/solid'

interface Props {
  confidence: number  // 0-100
  showPercentage?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showPercentage: false
})

const config = computed(() => {
  if (props.confidence >= 80) {
    return {
      icon: CheckCircleIcon,
      color: 'text-ai-confidence-high',
      label: 'High Confidence'
    }
  }
  if (props.confidence >= 50) {
    return {
      icon: ExclamationTriangleIcon,
      color: 'text-ai-confidence-medium',
      label: 'Medium Confidence'
    }
  }
  return {
    icon: XCircleIcon,
    color: 'text-ai-confidence-low',
    label: 'Low Confidence'
  }
})

const icon = computed(() => config.value.icon)
const color = computed(() => config.value.color)
const label = computed(() => config.value.label)
</script>
```

---

## README

```markdown
# YAM Server UI Kit

> Build once, use everywhere. Consistent, accessible, beautiful.

## What's Inside

- **50+ Vue 3 Components** based on frappe-ui
- **Design Tokens** for colors, typography, spacing
- **Storybook Documentation** for every component
- **Accessibility Built-In** (WCAG 2.1 AA compliant)
- **RTL Support** for Arabic and other RTL languages
- **Dark Mode** with theme switching
- **TypeScript** for type safety

## Installation

```bash
npm install @yam-server/ui-kit
```

## Usage

```vue
<script setup lang="ts">
import { Button, Card, AIAssistCard } from '@yam-server/ui-kit'
import '@yam-server/ui-kit/dist/style.css'
</script>

<template>
  <Card>
    <h2>Welcome to YAM Server</h2>
    <AIAssistCard
      title="Model Recommendation"
      suggestion="Based on your GPU (8GB VRAM), I recommend using Llama 3.2 3B with Q4 quantization for optimal performance."
      :confidence="85"
      @accept="applyRecommendation"
      @dismiss="dismissSuggestion"
    />
    <Button variant="primary">Get Started</Button>
  </Card>
</template>
```

## Component Categories

### Base Components
- Button, Input, Textarea, Select, Checkbox, Radio
- Card, Badge, Tag, Avatar
- Modal, Drawer, Dropdown, Tooltip

### AI Components
- AIAssistCard (suggestion display)
- ConfidenceIndicator (confidence visualization)
- SuggestionPanel (multiple suggestions)
- ModelSelector (choose model)
- TokenCounter (usage display)

### Data Components
- DataTable (sortable, filterable)
- SearchBar (with facets)
- Pagination
- EmptyState

### Layout Components
- AppLayout (sidebar + content)
- DashboardLayout (grid-based)
- FormLayout (responsive forms)

## Design Principles

1. **AI-Native:** Components designed for AI-assisted workflows
2. **Accessible:** WCAG 2.1 AA compliant by default
3. **Responsive:** Mobile-first, works on all screen sizes
4. **RTL-Ready:** Full support for right-to-left languages
5. **Themeable:** Light/dark mode, customizable tokens
6. **Performant:** Optimized bundles, lazy loading

## Storybook

View all components:

```bash
npm run storybook
# Open http://localhost:6006
```

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build library
npm run build

# Run tests
npm run test

# Lint
npm run lint
```

## Theming

Customize design tokens:

```typescript
import { createYamUI } from '@yam-server/ui-kit'

const yamUI = createYamUI({
  tokens: {
    colors: {
      primary: {
        500: '#your-brand-color'
      }
    },
    borderRadius: {
      default: '0.5rem'  // More rounded
    }
  }
})

app.use(yamUI)
```

## Accessibility

All components follow:
- Semantic HTML
- ARIA attributes
- Keyboard navigation
- Screen reader support
- Focus management
- Color contrast (WCAG AA)

Test with:
```bash
npm run test:a11y
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Component design guidelines
- Storybook story requirements
- Accessibility checklist
- Testing requirements
```

---

## Storybook Configuration

```typescript
// .storybook/main.ts
import type { StorybookConfig } from '@storybook/vue3-vite'

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',  // Accessibility testing
  ],
  framework: {
    name: '@storybook/vue3-vite',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
}

export default config
```

---

## Copilot Instructions

```markdown
## Critical Rules

1. **Accessibility First** - Every component must be WCAG 2.1 AA compliant
2. **Storybook Required** - No component without stories
3. **TypeScript Types** - All props and events must be typed
4. **RTL Testing** - Test components in RTL mode
5. **Design Tokens Only** - Never use hardcoded colors/spacing

## Component Checklist

Before merging a component:
- [ ] TypeScript types for all props
- [ ] Storybook stories (at least 3 variants)
- [ ] Unit tests (behavior, not implementation)
- [ ] Accessibility test passing
- [ ] RTL rendering correct
- [ ] Dark mode variant works
- [ ] Mobile responsive
- [ ] Documentation in story

## Never Do This

- ❌ Hardcode colors (use design tokens)
- ❌ Skip ARIA attributes
- ❌ Ignore keyboard navigation
- ❌ Use divs for buttons
- ❌ Forget focus indicators
```

---

**Status:** Ready for creation
