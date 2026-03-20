# Performance Optimization

Performance optimization patterns for React 19 + Vite SPA applications. Adapted from Vercel Engineering best practices with Next.js-specific patterns removed and Vite equivalents provided.

## Table of Contents

- [1. Async Optimization](#1-async-optimization)
  - [1.1 Defer Await Until Needed](#11-defer-await-until-needed)
  - [1.2 Promise.all() for Independent Operations](#12-promiseall-for-independent-operations)
  - [1.3 Dependency-Based Parallelization](#13-dependency-based-parallelization)
  - [1.4 Strategic Suspense Boundaries](#14-strategic-suspense-boundaries)
- [2. Bundle Size Optimization](#2-bundle-size-optimization)
  - [2.1 Barrel File Import Cost](#21-barrel-file-import-cost)
  - [2.2 Dynamic Imports with React.lazy()](#22-dynamic-imports-with-reactlazy)
  - [2.3 Conditional Module Loading](#23-conditional-module-loading)
  - [2.4 Defer Non-Critical Third-Party Libraries](#24-defer-non-critical-third-party-libraries)
  - [2.5 Preload Based on User Intent](#25-preload-based-on-user-intent)
- [3. Client-Side Data Fetching](#3-client-side-data-fetching)
  - [3.1 Use SWR for Automatic Deduplication](#31-use-swr-for-automatic-deduplication)
  - [3.2 Deduplicate Global Event Listeners](#32-deduplicate-global-event-listeners)
  - [3.3 Passive Event Listeners for Scrolling](#33-passive-event-listeners-for-scrolling)
  - [3.4 Version and Minimize localStorage Data](#34-version-and-minimize-localstorage-data)
- [4. Re-render Optimization](#4-re-render-optimization)
  - [4.1 Calculate Derived State During Rendering](#41-calculate-derived-state-during-rendering)
  - [4.2 Defer State Reads to Usage Point](#42-defer-state-reads-to-usage-point)
  - [4.3 Simple Expressions vs useMemo](#43-simple-expressions-vs-usememo)
  - [4.4 Extract Default Non-primitive Values](#44-extract-default-non-primitive-values-from-memoized-components)
  - [4.5 Extract to Memoized Components](#45-extract-to-memoized-components)
  - [4.6 Narrow Effect Dependencies](#46-narrow-effect-dependencies)
  - [4.7 Interaction Logic in Event Handlers](#47-interaction-logic-in-event-handlers)
  - [4.8 Subscribe to Derived State](#48-subscribe-to-derived-state)
  - [4.9 Use Functional setState Updates](#49-use-functional-setstate-updates)
  - [4.10 Lazy State Initialization](#410-lazy-state-initialization)
  - [4.11 Use Transitions for Non-Urgent Updates](#411-use-transitions-for-non-urgent-updates)
  - [4.12 Use useRef for Transient Values](#412-use-useref-for-transient-values)
- [5. Rendering Performance](#5-rendering-performance)
  - [5.1 Animate SVG Wrapper Instead of SVG Element](#51-animate-svg-wrapper-instead-of-svg-element)
  - [5.2 CSS content-visibility for Long Lists](#52-css-content-visibility-for-long-lists)
  - [5.3 Hoist Static JSX Elements](#53-hoist-static-jsx-elements)
  - [5.4 Use Activity Component for Show/Hide](#54-use-activity-component-for-showhide)
  - [5.5 Use Explicit Conditional Rendering](#55-use-explicit-conditional-rendering)
  - [5.6 Use useTransition Over Manual Loading States](#56-use-usetransition-over-manual-loading-states)
- [6. JavaScript Performance](#6-javascript-performance)
  - [6.1 Layout Thrashing](#61-layout-thrashing)
  - [6.2 Build Index Maps for Repeated Lookups](#62-build-index-maps-for-repeated-lookups)
  - [6.3 Cache Repeated Function Calls](#63-cache-repeated-function-calls)
  - [6.4 Cache Storage API Calls](#64-cache-storage-api-calls)
  - [6.5 Combined Array Iterations](#65-combined-array-iterations)
  - [6.6 Use Set/Map for O(1) Lookups](#66-use-setmap-for-o1-lookups)
  - [6.7 Use toSorted() for Immutability](#67-use-tosorted-for-immutability)
  - [6.8 Early Return from Functions](#68-early-return-from-functions)
  - [6.9 Hoisted RegExp Creation](#69-hoisted-regexp-creation)
  - [6.10 Early Length Check for Array Comparisons](#610-early-length-check-for-array-comparisons)
- [7. Advanced Patterns](#7-advanced-patterns)
  - [7.1 Initialize App Once, Not Per Mount](#71-initialize-app-once-not-per-mount)
  - [7.2 Store Event Handlers in Refs](#72-store-event-handlers-in-refs)
  - [7.3 useEffectEvent for Stable Callback Refs](#73-useeffectevent-for-stable-callback-refs)

---

## 1. Async Optimization

**Impact: CRITICAL**

Waterfalls are the #1 performance killer. Each sequential await adds full network latency.

### 1.1 Defer Await Until Needed

**Impact: HIGH**

Deferred `await` places the keyword in the branch where the value is consumed, avoiding blocking on unused code paths.

**Incorrect: blocks both branches**

```typescript
async function handleRequest(userId: string, skipProcessing: boolean) {
  const userData = await fetchUserData(userId)

  if (skipProcessing) {
    return { skipped: true }
  }

  return processUserData(userData)
}
```

**Correct: only blocks when needed**

```typescript
async function handleRequest(userId: string, skipProcessing: boolean) {
  if (skipProcessing) {
    return { skipped: true }
  }

  const userData = await fetchUserData(userId)
  return processUserData(userData)
}
```

### 1.2 Promise.all() for Independent Operations

**Impact: CRITICAL (2-10× improvement)**

Independent async operations support concurrent execution via `Promise.all()`.

**Incorrect: sequential execution, 3 round trips**

```typescript
const user = await fetchUser()
const posts = await fetchPosts()
const comments = await fetchComments()
```

**Correct: parallel execution, 1 round trip**

```typescript
const [user, posts, comments] = await Promise.all([
  fetchUser(),
  fetchPosts(),
  fetchComments()
])
```

### 1.3 Dependency-Based Parallelization

**Impact: CRITICAL (2-10× improvement)**

Operations with partial dependencies support starting independent work immediately while dependent chains resolve.

**Incorrect: profile waits for config unnecessarily**

```typescript
const [user, config] = await Promise.all([
  fetchUser(),
  fetchConfig()
])
const profile = await fetchProfile(user.id)
```

**Correct: config and profile run in parallel**

```typescript
const userPromise = fetchUser()
const profilePromise = userPromise.then(user => fetchProfile(user.id))

const [user, config, profile] = await Promise.all([
  userPromise,
  fetchConfig(),
  profilePromise
])
```

### 1.4 Strategic Suspense Boundaries

**Impact: HIGH (faster initial paint)**

Suspense boundaries show wrapper UI while data loads. In Vite SPA, `use()` unwraps promises inside Suspense.

**Incorrect: blocks entire page**

```tsx
function Page() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData().then(d => {
      setData(d)
      setLoading(false)
    })
  }, [])

  if (loading) return <Skeleton />

  return (
    <div>
      <Sidebar />
      <Header />
      <DataDisplay data={data} />
      <Footer />
    </div>
  )
}
```

**Correct: layout shows immediately, data streams in**

```tsx
function Page() {
  const dataPromise = useMemo(() => fetchData(), [])

  return (
    <div>
      <Sidebar />
      <Header />
      <Suspense fallback={<Skeleton />}>
        <DataDisplay dataPromise={dataPromise} />
      </Suspense>
      <Footer />
    </div>
  )
}

function DataDisplay({ dataPromise }: { dataPromise: Promise<Data> }) {
  const data = use(dataPromise)
  return <div>{data.content}</div>
}
```

Sidebar, Header, and Footer render immediately. Only DataDisplay waits for data.

---

## 2. Bundle Size Optimization

**Impact: CRITICAL**

Reducing initial bundle size improves Time to Interactive and Largest Contentful Paint.

### 2.1 Barrel File Import Cost

**Impact: CRITICAL (200-800ms import cost)**

Barrel file imports pull in the entire module tree. Direct source file imports load only what is referenced.

**Incorrect: imports entire library**

```tsx
import { Check, X, Menu } from 'lucide-react'
// Loads 1,583 modules

import { Button, TextField } from '@mui/material'
// Loads 2,225 modules
```

**Correct: imports only what you need**

```tsx
import Check from 'lucide-react/dist/esm/icons/check'
import X from 'lucide-react/dist/esm/icons/x'
import Menu from 'lucide-react/dist/esm/icons/menu'

import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
```

Libraries commonly affected: `lucide-react`, `@mui/material`, `@mui/icons-material`, `@tabler/icons-react`, `react-icons`, `@radix-ui/react-*`, `lodash`, `date-fns`, `rxjs`.

### 2.2 Dynamic Imports with React.lazy()

**Impact: CRITICAL (directly affects TTI and LCP)**

`React.lazy()` + `Suspense` lazy-loads large components not needed on initial render.

**Incorrect: Monaco bundles with main chunk ~300KB**

```tsx
import { MonacoEditor } from './monaco-editor'

function CodePanel({ code }: { code: string }) {
  return <MonacoEditor value={code} />
}
```

**Correct: Monaco loads on demand**

```tsx
import { lazy, Suspense } from 'react'

const MonacoEditor = lazy(() =>
  import('./monaco-editor').then(m => ({ default: m.MonacoEditor }))
)

function CodePanel({ code }: { code: string }) {
  return (
    <Suspense fallback={<div>Loading editor…</div>}>
      <MonacoEditor value={code} />
    </Suspense>
  )
}
```

### 2.3 Conditional Module Loading

**Impact: HIGH**

Load large data or modules only when a feature is activated.

```tsx
function AnimationPlayer({ enabled, setEnabled }: Props) {
  const [frames, setFrames] = useState<Frame[] | null>(null)

  useEffect(() => {
    if (enabled && !frames) {
      import('./animation-frames.js')
        .then(mod => setFrames(mod.frames))
        .catch(() => setEnabled(false))
    }
  }, [enabled, frames, setEnabled])

  if (!frames) return <Skeleton />
  return <Canvas frames={frames} />
}
```

### 2.4 Defer Non-Critical Third-Party Libraries

**Impact: MEDIUM**

Analytics, logging, and error tracking are non-blocking for user interaction and support lazy loading.

**Incorrect: blocks initial bundle**

```tsx
import { init as initAnalytics } from '@analytics/core'

function App() {
  useEffect(() => {
    initAnalytics({ /* config */ })
  }, [])

  return <Router />
}
```

**Correct: loads after initial render**

```tsx
function App() {
  useEffect(() => {
    import('@analytics/core').then(({ init }) => {
      init({ /* config */ })
    })
  }, [])

  return <Router />
}
```

### 2.5 Preload Based on User Intent

**Impact: MEDIUM**

Hover/focus events on triggers preload heavy bundles before navigation occurs.

```tsx
function EditorButton({ onClick }: { onClick: () => void }) {
  const preload = () => {
    void import('./monaco-editor')
  }

  return (
    <button
      onMouseEnter={preload}
      onFocus={preload}
      onClick={onClick}
    >
      Open Editor
    </button>
  )
}
```

---

## 3. Client-Side Data Fetching

**Impact: MEDIUM-HIGH**

### 3.1 Use SWR for Automatic Deduplication

**Impact: MEDIUM-HIGH**

SWR enables request deduplication, caching, and revalidation across component instances.

**Incorrect: no deduplication, each instance fetches**

```tsx
function UserList() {
  const [users, setUsers] = useState([])
  useEffect(() => {
    fetch('/api/users')
      .then(r => r.json())
      .then(setUsers)
  }, [])
}
```

**Correct: multiple instances share one request**

```tsx
import useSWR from 'swr'

function UserList() {
  const { data: users } = useSWR('/api/users', fetcher)
}
```

**For mutations:**

```tsx
import useSWRMutation from 'swr/mutation'

function UpdateButton() {
  const { trigger } = useSWRMutation('/api/user', updateUser)
  return <button onClick={() => trigger()}>Update</button>
}
```

### 3.2 Deduplicate Global Event Listeners

**Impact: LOW**

`useSWRSubscription()` shares global event listeners across component instances, reducing N listeners to 1.

**Incorrect: N instances = N listeners**

```tsx
function useKeyboardShortcut(key: string, callback: () => void) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.metaKey && e.key === key) {
        callback()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [key, callback])
}
```

**Correct: N instances = 1 listener**

```tsx
import useSWRSubscription from 'swr/subscription'

const keyCallbacks = new Map<string, Set<() => void>>()

function useKeyboardShortcut(key: string, callback: () => void) {
  useEffect(() => {
    if (!keyCallbacks.has(key)) {
      keyCallbacks.set(key, new Set())
    }
    keyCallbacks.get(key)!.add(callback)

    return () => {
      const set = keyCallbacks.get(key)
      if (set) {
        set.delete(callback)
        if (set.size === 0) keyCallbacks.delete(key)
      }
    }
  }, [key, callback])

  useSWRSubscription('global-keydown', () => {
    const handler = (e: KeyboardEvent) => {
      if (e.metaKey && keyCallbacks.has(e.key)) {
        keyCallbacks.get(e.key)!.forEach(cb => cb())
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  })
}
```

### 3.3 Passive Event Listeners for Scrolling

**Impact: MEDIUM**

Without `{ passive: true }`, the browser must wait for the listener to finish before it can scroll, because the listener might call `preventDefault()`. Marking a listener as passive tells the browser it is safe to scroll immediately in parallel, eliminating scroll jank on touch and wheel events.

**Incorrect:**

```typescript
document.addEventListener('touchstart', handleTouch)
document.addEventListener('wheel', handleWheel)
```

**Correct:**

```typescript
document.addEventListener('touchstart', handleTouch, { passive: true })
document.addEventListener('wheel', handleWheel, { passive: true })
```

Use passive when: tracking/analytics, logging, any listener that doesn't call `preventDefault()`.

### 3.4 Version and Minimize localStorage Data

**Impact: MEDIUM**

Add version prefix to keys and store only needed fields.

```typescript
const VERSION = 'v2'

function saveConfig(config: { theme: string; language: string }) {
  try {
    localStorage.setItem(`userConfig:${VERSION}`, JSON.stringify(config))
  } catch {
    // Throws in incognito, quota exceeded, or disabled
  }
}

function loadConfig() {
  try {
    const data = localStorage.getItem(`userConfig:${VERSION}`)
    return data ? JSON.parse(data) : null
  } catch {
    return null
  }
}
```

Always wrap in try-catch. `getItem()` and `setItem()` throw in incognito/private browsing.

---

## 4. Re-render Optimization

**Impact: MEDIUM**

### 4.1 Calculate Derived State During Rendering

**Impact: MEDIUM**

Values computable from current props/state are derived during render, eliminating redundant state and effects.

**Incorrect: redundant state and effect**

```tsx
function Form() {
  const [firstName, setFirstName] = useState('First')
  const [lastName, setLastName] = useState('Last')
  const [fullName, setFullName] = useState('')

  useEffect(() => {
    setFullName(firstName + ' ' + lastName)
  }, [firstName, lastName])

  return <p>{fullName}</p>
}
```

**Correct: derive during render**

```tsx
function Form() {
  const [firstName, setFirstName] = useState('First')
  const [lastName, setLastName] = useState('Last')
  const fullName = firstName + ' ' + lastName

  return <p>{fullName}</p>
}
```

### 4.2 Defer State Reads to Usage Point

**Impact: MEDIUM**

Reading dynamic state only inside callbacks avoids subscribing to changes that do not affect render output.

**Incorrect: subscribes to all URL changes**

```tsx
function ShareButton({ chatId }: { chatId: string }) {
  const [searchParams] = useSearchParams()

  const handleShare = () => {
    const ref = searchParams.get('ref')
    shareChat(chatId, { ref })
  }

  return <button onClick={handleShare}>Share</button>
}
```

**Correct: reads on demand**

```tsx
function ShareButton({ chatId }: { chatId: string }) {
  const handleShare = () => {
    const params = new URLSearchParams(window.location.search)
    const ref = params.get('ref')
    shareChat(chatId, { ref })
  }

  return <button onClick={handleShare}>Share</button>
}
```

### 4.3 Simple Expressions vs useMemo

**Impact: LOW-MEDIUM**

`useMemo` itself has overhead: it stores the previous value, compares dependencies on every render, and adds memory pressure. For cheap operations like boolean OR or string concatenation, that bookkeeping costs more than just re-computing the value. Reserve `useMemo` for genuinely expensive work (large list transforms, deep object construction).

**Incorrect:**

```tsx
const isLoading = useMemo(() => {
  return user.isLoading || notifications.isLoading
}, [user.isLoading, notifications.isLoading])
```

**Correct:**

```tsx
const isLoading = user.isLoading || notifications.isLoading
```

### 4.4 Extract Default Non-primitive Values from Memoized Components

**Impact: MEDIUM**

Default non-primitive parameter values create new instances on every render, breaking `memo()`.

**Incorrect:**

```tsx
const UserAvatar = memo(function UserAvatar({ onClick = () => {} }: Props) {
  // ...
})
```

**Correct:**

```tsx
const NOOP = () => {};

const UserAvatar = memo(function UserAvatar({ onClick = NOOP }: Props) {
  // ...
})
```

### 4.5 Extract to Memoized Components

**Impact: MEDIUM**

Memoized components encapsulate expensive work, enabling early returns that skip computation entirely.

**Incorrect: computes avatar even when loading**

```tsx
function Profile({ user, loading }: Props) {
  const avatar = useMemo(() => {
    const id = computeAvatarId(user)
    return <Avatar id={id} />
  }, [user])

  if (loading) return <Skeleton />
  return <div>{avatar}</div>
}
```

**Correct: skips computation when loading**

```tsx
const UserAvatar = memo(function UserAvatar({ user }: { user: User }) {
  const id = useMemo(() => computeAvatarId(user), [user])
  return <Avatar id={id} />
})

function Profile({ user, loading }: Props) {
  if (loading) return <Skeleton />
  return (
    <div>
      <UserAvatar user={user} />
    </div>
  )
}
```

> If React Compiler is enabled, manual `memo()` and `useMemo()` are unnecessary.

### 4.6 Narrow Effect Dependencies

**Impact: LOW**

Objects create a new reference on every render even when their contents haven't changed, causing effects to re-run unnecessarily. Extracting the specific primitive value you depend on (e.g., `user.id` instead of `user`) ensures the effect only fires when that value actually changes.

```tsx
// ❌ Re-runs on any user field change
useEffect(() => {
  console.log(user.id)
}, [user])

// ✅ Re-runs only when id changes
useEffect(() => {
  console.log(user.id)
}, [user.id])
```

**Derived state outside effect:**

```tsx
// ❌ Runs on width=767, 766, 765...
useEffect(() => {
  if (width < 768) enableMobileMode()
}, [width])

// ✅ Runs only on boolean transition
const isMobile = width < 768
useEffect(() => {
  if (isMobile) enableMobileMode()
}, [isMobile])
```

### 4.7 Interaction Logic in Event Handlers

**Impact: MEDIUM**

Encoding a user action as state (`setSubmitted(true)`) then reacting to it in `useEffect` creates an extra render cycle: one to set the flag, another after the effect runs. It also couples the side effect to every dependency of the effect (e.g., `theme`), causing unintended re-fires. Placing the logic directly in the event handler runs it once, synchronously, with no extra renders.

**Incorrect:**

```tsx
function Form() {
  const [submitted, setSubmitted] = useState(false)
  const theme = useContext(ThemeContext)

  useEffect(() => {
    if (submitted) {
      post('/api/register')
      showToast('Registered', theme)
    }
  }, [submitted, theme])

  return <button onClick={() => setSubmitted(true)}>Submit</button>
}
```

**Correct:**

```tsx
function Form() {
  const theme = useContext(ThemeContext)

  function handleSubmit() {
    post('/api/register')
    showToast('Registered', theme)
  }

  return <button onClick={handleSubmit}>Submit</button>
}
```

### 4.8 Subscribe to Derived State

**Impact: MEDIUM**

Derived boolean state changes less frequently than continuous values, reducing re-render frequency.

**Incorrect: re-renders on every pixel change**

```tsx
function Sidebar() {
  const width = useWindowWidth()
  const isMobile = width < 768
  return <nav className={isMobile ? 'mobile' : 'desktop'} />
}
```

**Correct: re-renders only when boolean changes**

```tsx
function Sidebar() {
  const isMobile = useMediaQuery('(max-width: 767px)')
  return <nav className={isMobile ? 'mobile' : 'desktop'} />
}
```

### 4.9 Use Functional setState Updates

**Impact: MEDIUM**

Prevents stale closures and unnecessary callback recreations.

**Incorrect: requires state as dependency**

```tsx
const addItems = useCallback((newItems: Item[]) => {
  setItems([...items, ...newItems])
}, [items]) // items dependency causes recreations
```

**Correct: stable callbacks, no stale closures**

```tsx
const addItems = useCallback((newItems: Item[]) => {
  setItems(curr => [...curr, ...newItems])
}, []) // No dependencies needed
```

**When to use functional updates:** any `setState` that depends on the current state value, inside `useCallback`/`useMemo`, event handlers that reference state, async operations.

**When direct updates are fine:** setting to a static value (`setCount(0)`), setting from props/arguments only, state doesn't depend on previous value.

### 4.10 Lazy State Initialization

**Impact: MEDIUM**

A function passed to `useState` runs only on initial render; a direct expression runs on every render.

**Incorrect: runs on every render**

```tsx
const [settings, setSettings] = useState(
  JSON.parse(localStorage.getItem('settings') || '{}')
)
```

**Correct: runs only once**

```tsx
const [settings, setSettings] = useState(() => {
  const stored = localStorage.getItem('settings')
  return stored ? JSON.parse(stored) : {}
})
```

### 4.11 Use Transitions for Non-Urgent Updates

**Impact: MEDIUM**

```tsx
import { startTransition } from 'react'

function ScrollTracker() {
  const [scrollY, setScrollY] = useState(0)
  useEffect(() => {
    const handler = () => {
      startTransition(() => setScrollY(window.scrollY))
    }
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])
}
```

### 4.12 Use useRef for Transient Values

**Impact: MEDIUM**

When a value changes frequently and you don't need a re-render on every update, use `useRef` instead of `useState`.

**Incorrect: renders every update**

```tsx
function Tracker() {
  const [lastX, setLastX] = useState(0)

  useEffect(() => {
    const onMove = (e: MouseEvent) => setLastX(e.clientX)
    window.addEventListener('mousemove', onMove)
    return () => window.removeEventListener('mousemove', onMove)
  }, [])

  return <div style={{ left: lastX }} />
}
```

**Correct: no re-render for tracking**

```tsx
function Tracker() {
  const lastXRef = useRef(0)
  const dotRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      lastXRef.current = e.clientX
      if (dotRef.current) {
        dotRef.current.style.transform = `translateX(${e.clientX}px)`
      }
    }
    window.addEventListener('mousemove', onMove)
    return () => window.removeEventListener('mousemove', onMove)
  }, [])

  return <div ref={dotRef} style={{ transform: 'translateX(0px)' }} />
}
```

---

## 5. Rendering Performance

**Impact: MEDIUM**

### 5.1 Animate SVG Wrapper Instead of SVG Element

**Impact: LOW**

Browsers promote HTML `<div>` elements to their own GPU compositing layer when transforms/animations are applied, enabling hardware-accelerated rendering. SVG elements are not promoted the same way — animating them directly forces the browser to repaint on the CPU each frame. Wrapping the SVG in a `<div>` lets the GPU handle the animation.

```tsx
// ❌ No hardware acceleration
<svg className="animate-spin" width="24" height="24" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="10" stroke="currentColor" />
</svg>

// ✅ Hardware accelerated
<div className="animate-spin">
  <svg width="24" height="24" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="10" stroke="currentColor" />
  </svg>
</div>
```

### 5.2 CSS content-visibility for Long Lists

**Impact: HIGH**

```css
.message-item {
  content-visibility: auto;
  contain-intrinsic-size: 0 80px;
}
```

For 1000 items, browser skips layout/paint for ~990 off-screen items.

### 5.3 Hoist Static JSX Elements

**Impact: LOW**

```tsx
// ❌ Recreates element every render
function LoadingSkeleton() {
  return <div className="animate-pulse h-20 bg-gray-200" />
}

// ✅ Reuses same element
const loadingSkeleton = (
  <div className="animate-pulse h-20 bg-gray-200" />
)
```

> If React Compiler is enabled, it automatically hoists static JSX.

### 5.4 Use Activity Component for Show/Hide

**Impact: MEDIUM**

```tsx
import { Activity } from 'react'

function Dropdown({ isOpen }: Props) {
  return (
    <Activity mode={isOpen ? 'visible' : 'hidden'}>
      <ExpensiveMenu />
    </Activity>
  )
}
```

Avoids expensive re-renders and state loss.

### 5.5 Use Explicit Conditional Rendering

**Impact: LOW**

JavaScript's `&&` operator returns the left-hand value when it's falsy — so `0 && <JSX>` renders the string `"0"` instead of nothing. Using an explicit comparison (`count > 0`) ensures a boolean left-hand side, which React correctly treats as "render nothing" when false.

```tsx
// ❌ Renders "0" when count is 0
{count && <span className="badge">{count}</span>}

// ✅ Renders nothing when count is 0
{count > 0 ? <span className="badge">{count}</span> : null}
```

### 5.6 Use useTransition Over Manual Loading States

**Impact: LOW**

```tsx
import { useTransition, useState } from 'react'

function SearchResults() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isPending, startTransition] = useTransition()

  const handleSearch = (value: string) => {
    setQuery(value)
    startTransition(async () => {
      const data = await fetchResults(value)
      setResults(data)
    })
  }

  return (
    <>
      <input onChange={(e) => handleSearch(e.target.value)} />
      {isPending && <Spinner />}
      <ResultsList results={results} />
    </>
  )
}
```

---

## 6. JavaScript Performance

**Impact: LOW-MEDIUM**

### 6.1 Layout Thrashing

**Impact: MEDIUM**

Interleaving style writes with layout reads forces synchronous reflow on each read. Batching writes then reading once avoids this.

```typescript
// ❌ Forces reflow on each read
element.style.width = '100px'
const width = element.offsetWidth  // Forces reflow
element.style.height = '200px'
const height = element.offsetHeight  // Forces another reflow

// ✅ Batch writes, then read once
element.style.width = '100px'
element.style.height = '200px'
const { width, height } = element.getBoundingClientRect()
```

Prefer CSS classes over inline styles when possible.

### 6.2 Build Index Maps for Repeated Lookups

**Impact: LOW-MEDIUM**

```typescript
// ❌ O(n) per lookup
orders.map(order => ({
  ...order,
  user: users.find(u => u.id === order.userId)
}))

// ✅ O(1) per lookup
const userById = new Map(users.map(u => [u.id, u]))
orders.map(order => ({
  ...order,
  user: userById.get(order.userId)
}))
```

### 6.3 Cache Repeated Function Calls

**Impact: MEDIUM**

```typescript
const slugifyCache = new Map<string, string>()

function cachedSlugify(text: string): string {
  if (slugifyCache.has(text)) return slugifyCache.get(text)!
  const result = slugify(text)
  slugifyCache.set(text, result)
  return result
}
```

### 6.4 Cache Storage API Calls

**Impact: LOW-MEDIUM**

```typescript
const storageCache = new Map<string, string | null>()

function getLocalStorage(key: string) {
  if (!storageCache.has(key)) {
    storageCache.set(key, localStorage.getItem(key))
  }
  return storageCache.get(key)
}

function setLocalStorage(key: string, value: string) {
  localStorage.setItem(key, value)
  storageCache.set(key, value)
}
```

Invalidate on external changes:

```typescript
window.addEventListener('storage', (e) => {
  if (e.key) storageCache.delete(e.key)
})
```

### 6.5 Combined Array Iterations

**Impact: LOW-MEDIUM**

```typescript
// ❌ 3 iterations
const admins = users.filter(u => u.isAdmin)
const testers = users.filter(u => u.isTester)
const inactive = users.filter(u => !u.isActive)

// ✅ 1 iteration
const admins: User[] = []
const testers: User[] = []
const inactive: User[] = []

for (const user of users) {
  if (user.isAdmin) admins.push(user)
  if (user.isTester) testers.push(user)
  if (!user.isActive) inactive.push(user)
}
```

### 6.6 Use Set/Map for O(1) Lookups

**Impact: LOW-MEDIUM**

```typescript
// ❌ O(n) per check
const allowedIds = ['a', 'b', 'c']
items.filter(item => allowedIds.includes(item.id))

// ✅ O(1) per check
const allowedIds = new Set(['a', 'b', 'c'])
items.filter(item => allowedIds.has(item.id))
```

### 6.7 Use toSorted() for Immutability

**Impact: MEDIUM-HIGH**

```typescript
// ❌ Mutates the users prop array
const sorted = users.sort((a, b) => a.name.localeCompare(b.name))

// ✅ Creates new sorted array
const sorted = users.toSorted((a, b) => a.name.localeCompare(b.name))
```

Other immutable methods: `.toReversed()`, `.toSpliced()`, `.with()`.

### 6.8 Early Return from Functions

**Impact: LOW-MEDIUM**

```typescript
// ❌ Processes all items even after finding answer
function validateUsers(users: User[]) {
  let hasError = false
  let errorMessage = ''
  for (const user of users) {
    if (!user.email) { hasError = true; errorMessage = 'Email required' }
    if (!user.name) { hasError = true; errorMessage = 'Name required' }
  }
  return hasError ? { valid: false, error: errorMessage } : { valid: true }
}

// ✅ Returns immediately on first error
function validateUsers(users: User[]) {
  for (const user of users) {
    if (!user.email) return { valid: false, error: 'Email required' }
    if (!user.name) return { valid: false, error: 'Name required' }
  }
  return { valid: true }
}
```

### 6.9 Hoisted RegExp Creation

**Impact: LOW-MEDIUM**

```tsx
// ❌ New RegExp every render
function Highlighter({ text, query }: Props) {
  const regex = new RegExp(`(${query})`, 'gi')
  const parts = text.split(regex)
  return <>{parts.map((part, i) => ...)}</>
}

// ✅ Memoize
function Highlighter({ text, query }: Props) {
  const regex = useMemo(
    () => new RegExp(`(${escapeRegex(query)})`, 'gi'),
    [query]
  )
  const parts = text.split(regex)
  return <>{parts.map((part, i) => ...)}</>
}
```

### 6.10 Early Length Check for Array Comparisons

**Impact: MEDIUM-HIGH**

```typescript
function hasChanges(current: string[], original: string[]) {
  if (current.length !== original.length) return true

  const currentSorted = current.toSorted()
  const originalSorted = original.toSorted()
  for (let i = 0; i < currentSorted.length; i++) {
    if (currentSorted[i] !== originalSorted[i]) return true
  }
  return false
}
```

---

## 7. Advanced Patterns

**Impact: LOW**

### 7.1 Initialize App Once, Not Per Mount

**Impact: LOW-MEDIUM**

```tsx
let didInit = false

function App() {
  useEffect(() => {
    if (didInit) return
    didInit = true
    loadFromStorage()
    checkAuthToken()
  }, [])

  // ...
}
```

### 7.2 Store Event Handlers in Refs

**Impact: LOW**

```tsx
import { useEffectEvent } from 'react'

function useWindowEvent(event: string, handler: (e: Event) => void) {
  const onEvent = useEffectEvent(handler)

  useEffect(() => {
    window.addEventListener(event, onEvent)
    return () => window.removeEventListener(event, onEvent)
  }, [event])
}
```

### 7.3 useEffectEvent for Stable Callback Refs

**Impact: LOW**

```tsx
import { useEffectEvent } from 'react'

function SearchInput({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState('')
  const onSearchEvent = useEffectEvent(onSearch)

  useEffect(() => {
    const timeout = setTimeout(() => onSearchEvent(query), 300)
    return () => clearTimeout(timeout)
  }, [query])
}
```

---

## References

1. [https://react.dev](https://react.dev)
2. [https://react.dev/reference/react/use](https://react.dev/reference/react/use)
3. [https://react.dev/learn/you-might-not-need-an-effect](https://react.dev/learn/you-might-not-need-an-effect)
4. [https://react.dev/reference/react/useTransition](https://react.dev/reference/react/useTransition)
5. [https://swr.vercel.app](https://swr.vercel.app)
6. [https://github.com/shuding/better-all](https://github.com/shuding/better-all)
7. [https://vercel.com/blog/how-we-optimized-package-imports-in-next-js](https://vercel.com/blog/how-we-optimized-package-imports-in-next-js)
