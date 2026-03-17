# YAM Server UI/UX Design System

> **Purpose:** This document defines the UI/UX design system for YAM Server applications, based on [Frappe UI](https://github.com/frappe/frappe-ui) and following modern design principles.

---

## Design Philosophy

The YAM Server UI design system is built on three principles:

1. **Consistency** - Same patterns across all YAM Server touchpoints
2. **Accessibility** - WCAG 2.1 AA compliance, keyboard navigation, screen reader support
3. **Composability** - Small, reusable components that combine into complex interfaces

Unlike generic design systems, this one is purpose-built for:

- **Business applications** - Dense information, forms, tables, workflows
- **AI-assisted interfaces** - Suggestion cards, confidence indicators, review flows
- **Multi-modal interfaces** - Frappe Desk (desktop), mobile PWA, SMS (text-only)
- **Offline-first** - Works without constant connectivity

---

## Technology Foundation

### Base: Frappe UI

[Frappe UI](https://github.com/frappe/frappe-ui) is a Vue 3 component library developed by Frappe Technologies for building modern web applications.

**Why Frappe UI?**

- ✅ **Vue 3 + Vite** - Modern, fast, developer-friendly
- ✅ **Tailwind CSS** - Utility-first styling, easy customization
- ✅ **Headless components** - Accessible primitives (Headless UI)
- ✅ **Frappe integration** - Native compatibility with Frappe backend
- ✅ **Open source** - MIT license, community-driven
- ✅ **Production-tested** - Used by Frappe Cloud, ERPNext

**Core dependencies:**
```json
{
  "vue": "^3.3.0",
  "vite": "^5.0.0",
  "tailwindcss": "^3.4.0",
  "@headlessui/vue": "^1.7.0",
  "@heroicons/vue": "^2.1.0",
  "frappe-ui": "^0.1.0"
}
```

---

## Design Tokens

Design tokens are the atomic values that define the visual language: colors, typography, spacing, shadows, etc.

### Color Palette

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Brand colors
        'yam-primary': {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',  // Primary brand color
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },

        // Semantic colors
        'yam-success': {
          DEFAULT: '#10b981',
          light: '#d1fae5',
          dark: '#047857'
        },
        'yam-warning': {
          DEFAULT: '#f59e0b',
          light: '#fef3c7',
          dark: '#d97706'
        },
        'yam-danger': {
          DEFAULT: '#ef4444',
          light: '#fee2e2',
          dark: '#dc2626'
        },
        'yam-info': {
          DEFAULT: '#3b82f6',
          light: '#dbeafe',
          dark: '#1e40af'
        },

        // Neutral colors (Frappe default)
        'gray': {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        }
      }
    }
  }
}
```

### Typography

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['Fira Code', 'monospace'],
        'arabic': ['Cairo', 'sans-serif']  // For RTL support
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],     // 12px
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],  // 14px
        'base': ['1rem', { lineHeight: '1.5rem' }],     // 16px
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],  // 18px
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],   // 20px
        '2xl': ['1.5rem', { lineHeight: '2rem' }],      // 24px
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],   // 36px
      }
    }
  }
}
```

### Spacing Scale

```javascript
// Following Tailwind's default scale (4px base unit)
// 0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 56, 64
// Maps to: 0px, 2px, 4px, 6px, 8px, 10px, 12px, 16px, 20px, ...
```

### Shadows and Elevation

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      }
    }
  }
}
```

---

## Component Library

### Core Components (from Frappe UI)

The `yam-server-ui-kit` repository extends Frappe UI with YAM-specific components.

**Base components (Frappe UI):**
- `Button` - Primary, secondary, tertiary variants
- `Input` - Text, number, date, time fields
- `Select` - Dropdown selector
- `Checkbox` - Boolean input
- `Radio` - Single choice from options
- `Badge` - Status indicators
- `Avatar` - User avatars
- `Card` - Content containers
- `Dialog` - Modal dialogs
- `Dropdown` - Contextual menus
- `Toast` - Notifications
- `Popover` - Contextual help
- `Tabs` - Content organization
- `Table` - Data tables
- `Pagination` - Table navigation

**YAM-specific components (custom):**
- `AIAssistCard` - AI suggestion display
- `ConfidenceIndicator` - AI confidence meter
- `ReviewPanel` - AI output review interface
- `ApprovalFlow` - Workflow approval UI
- `QCSampleCard` - Quality control test display
- `LotTimeline` - Supply chain event timeline
- `SiteSelector` - Multi-site navigation

### Component Example: AIAssistCard

```vue
<!-- In yam-server-ui-kit/src/components/AIAssistCard.vue -->
<template>
  <Card class="ai-assist-card border-l-4 border-yam-primary-500">
    <div class="flex items-start gap-3">
      <!-- AI Icon -->
      <div class="flex-shrink-0">
        <SparklesIcon class="h-5 w-5 text-yam-primary-500" />
      </div>

      <!-- Content -->
      <div class="flex-1">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-medium text-gray-900">
            {{ title }}
          </h3>
          <ConfidenceIndicator :score="confidence" />
        </div>

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
            Accept Suggestion
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

    <!-- Attribution -->
    <div class="mt-3 pt-3 border-t border-gray-200">
      <p class="text-xs text-gray-500">
        Powered by {{ modelName }} • Generated {{ timestamp }}
      </p>
    </div>
  </Card>
</template>

<script setup>
import { Card, Button } from 'frappe-ui'
import { SparklesIcon } from '@heroicons/vue/24/outline'
import ConfidenceIndicator from './ConfidenceIndicator.vue'

defineProps({
  title: String,
  suggestion: String,
  confidence: Number,
  modelName: String,
  timestamp: String
})

defineEmits(['accept', 'edit', 'dismiss'])
</script>

<style scoped>
.ai-assist-card {
  background: linear-gradient(to right, #f0f9ff 0%, #ffffff 100%);
}
</style>
```

### Component Example: ConfidenceIndicator

```vue
<!-- In yam-server-ui-kit/src/components/ConfidenceIndicator.vue -->
<template>
  <div class="flex items-center gap-2">
    <div class="flex items-center gap-1">
      <div
        v-for="i in 5"
        :key="i"
        class="h-1 w-6 rounded-full"
        :class="i <= filledBars ? barColor : 'bg-gray-200'"
      />
    </div>
    <span class="text-xs text-gray-600">
      {{ Math.round(score * 100) }}%
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  score: {
    type: Number,
    required: true,
    validator: (val) => val >= 0 && val <= 1
  }
})

const filledBars = computed(() => Math.ceil(props.score * 5))

const barColor = computed(() => {
  if (props.score >= 0.8) return 'bg-yam-success'
  if (props.score >= 0.6) return 'bg-yam-info'
  if (props.score >= 0.4) return 'bg-yam-warning'
  return 'bg-yam-danger'
})
</script>
```

---

## Layout Patterns

### Desktop Layout (Frappe Desk Style)

```
┌─────────────────────────────────────────────────────┐
│  Top Nav (logo, search, notifications, profile)    │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│  Sidebar │  Main Content Area                       │
│          │  ┌────────────────────────────────────┐  │
│  - Nav   │  │  Page Header                       │  │
│  - Menu  │  ├────────────────────────────────────┤  │
│  - Items │  │  Breadcrumb                        │  │
│          │  ├────────────────────────────────────┤  │
│          │  │                                    │  │
│          │  │  Page Content                      │  │
│          │  │                                    │  │
│          │  │                                    │  │
│          │  └────────────────────────────────────┘  │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

### Mobile Layout (PWA)

```
┌─────────────────┐
│ Top App Bar     │  ← Hamburger, title, actions
├─────────────────┤
│                 │
│  Main Content   │  ← Full width, scrollable
│                 │
│  [FAB]          │  ← Floating action button
│                 │
├─────────────────┤
│ Bottom Nav      │  ← Tab bar (3-5 items)
└─────────────────┘
```

---

## Accessibility

### WCAG 2.1 AA Compliance

**Requirements:**
- ✅ Color contrast ratio ≥ 4.5:1 for normal text
- ✅ Color contrast ratio ≥ 3:1 for large text (18pt+)
- ✅ Keyboard navigation for all interactive elements
- ✅ Focus indicators visible on all focusable elements
- ✅ Screen reader support (ARIA labels, roles, live regions)
- ✅ Form labels and error messages
- ✅ Skip navigation links
- ✅ Descriptive link text (no "click here")

### Keyboard Navigation

```javascript
// Component example with keyboard support
<template>
  <div
    role="button"
    tabindex="0"
    @click="handleAction"
    @keydown.enter="handleAction"
    @keydown.space.prevent="handleAction"
    class="focus:ring-2 focus:ring-yam-primary-500 focus:outline-none"
  >
    {{ label }}
  </div>
</template>
```

### Screen Reader Support

```vue
<!-- Example: AI suggestion card with proper ARIA -->
<template>
  <div
    role="region"
    aria-labelledby="ai-suggestion-title"
    aria-live="polite"
    class="ai-assist-card"
  >
    <h3 id="ai-suggestion-title" class="sr-only">
      AI Suggestion
    </h3>

    <p aria-label="Suggestion text">
      {{ suggestion }}
    </p>

    <div role="group" aria-label="Actions">
      <Button aria-label="Accept this suggestion">
        Accept
      </Button>
      <Button aria-label="Edit this suggestion">
        Edit
      </Button>
      <Button aria-label="Dismiss this suggestion">
        Dismiss
      </Button>
    </div>
  </div>
</template>
```

---

## RTL (Right-to-Left) Support

For Arabic and other RTL languages:

```vue
<!-- Auto-detect and apply RTL -->
<template>
  <div :dir="isRTL ? 'rtl' : 'ltr'" :lang="currentLocale">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const isRTL = computed(() => ['ar', 'he', 'fa', 'ur'].includes(locale.value))
</script>
```

**RTL-safe CSS:**
```css
/* Use logical properties instead of directional */
/* ❌ Bad: */
.card {
  margin-left: 1rem;
  text-align: left;
}

/* ✅ Good: */
.card {
  margin-inline-start: 1rem;
  text-align: start;
}
```

---

## Responsive Design

### Breakpoints

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    screens: {
      'sm': '640px',   // Mobile landscape
      'md': '768px',   // Tablet
      'lg': '1024px',  // Desktop
      'xl': '1280px',  // Large desktop
      '2xl': '1536px', // Extra large desktop
    }
  }
}
```

### Component Responsiveness

```vue
<template>
  <!-- Desktop: side-by-side -->
  <!-- Mobile: stacked -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <Card>Content 1</Card>
    <Card>Content 2</Card>
  </div>

  <!-- Hide on mobile, show on desktop -->
  <div class="hidden md:block">
    Desktop only content
  </div>

  <!-- Show on mobile, hide on desktop -->
  <div class="block md:hidden">
    Mobile only content
  </div>
</template>
```

---

## Dark Mode Support

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',  // or 'media' for system preference
  theme: {
    extend: {
      // Define dark mode colors
    }
  }
}
```

```vue
<template>
  <div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <Button class="bg-yam-primary-500 hover:bg-yam-primary-600 dark:bg-yam-primary-400 dark:hover:bg-yam-primary-500">
      Click me
    </Button>
  </div>
</template>
```

---

## Animation and Transitions

### Micro-interactions

```vue
<template>
  <!-- Smooth button hover -->
  <Button class="transition-all duration-150 hover:scale-105 active:scale-95">
    Interactive Button
  </Button>

  <!-- Loading spinner -->
  <div class="animate-spin h-5 w-5 border-2 border-yam-primary-500 border-t-transparent rounded-full" />

  <!-- Fade in/out -->
  <transition name="fade">
    <div v-if="show">Fading content</div>
  </transition>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```

### Page Transitions

```javascript
// In router
const router = createRouter({
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})
```

---

## Form Patterns

### AI-Assisted Form

```vue
<template>
  <form @submit.prevent="handleSubmit">
    <!-- Traditional input -->
    <Input
      v-model="invoiceNumber"
      label="Invoice Number"
      placeholder="INV-001"
      required
    />

    <!-- AI-assisted input with suggestion -->
    <div class="relative">
      <Input
        v-model="totalAmount"
        label="Total Amount"
        type="number"
        placeholder="0.00"
      />

      <!-- AI suggestion overlay -->
      <div
        v-if="aiSuggestion"
        class="absolute top-full mt-2 left-0 right-0 z-10"
      >
        <AIAssistCard
          title="Suggested Amount"
          :suggestion="`Detected amount: ${aiSuggestion.amount}`"
          :confidence="aiSuggestion.confidence"
          @accept="totalAmount = aiSuggestion.amount"
          @dismiss="aiSuggestion = null"
        />
      </div>
    </div>

    <!-- Submit -->
    <div class="flex gap-2">
      <Button type="submit" variant="primary">
        Save Invoice
      </Button>
      <Button
        type="button"
        variant="secondary"
        @click="requestAISuggestion"
        :loading="loadingAI"
      >
        <SparklesIcon class="h-4 w-4 mr-1" />
        Get AI Suggestion
      </Button>
    </div>
  </form>
</template>
```

---

## Storybook Documentation

The `yam-server-ui-kit` repository includes Storybook for component documentation and testing.

```javascript
// Button.stories.js
export default {
  title: 'Components/Button',
  component: Button,
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'ghost', 'danger']
    },
    size: {
      control: 'select',
      options: ['xs', 'sm', 'md', 'lg']
    }
  }
}

export const Primary = {
  args: {
    variant: 'primary',
    children: 'Click me'
  }
}

export const WithIcon = {
  args: {
    variant: 'primary',
    children: 'Save',
    icon: 'check'
  }
}

export const Loading = {
  args: {
    variant: 'primary',
    children: 'Processing...',
    loading: true
  }
}
```

---

## Design-to-Code Workflow

### 1. Design in Figma

- Use Frappe UI design tokens
- Follow component patterns
- Document interactions
- Export assets (icons, illustrations)

### 2. Build in yam-server-ui-kit

- Implement as Vue 3 SFC
- Use Tailwind CSS utilities
- Add Storybook stories
- Write accessibility tests

### 3. Publish to npm

```bash
cd yam-server-ui-kit
npm version patch
npm publish
```

### 4. Consume in applications

```bash
cd yam-server-business
npm install @yam/ui-kit@latest
```

```vue
<script setup>
import { AIAssistCard, Button } from '@yam/ui-kit'
</script>

<template>
  <AIAssistCard ... />
</template>
```

---

## Resources

- [Frappe UI GitHub](https://github.com/frappe/frappe-ui)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Headless UI](https://headlessui.com/)
- [Hero Icons](https://heroicons.com/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Storybook](https://storybook.js.org/)

---

**Principle:** Build once, use everywhere. The UI kit is the source of truth for all YAM Server interfaces.
