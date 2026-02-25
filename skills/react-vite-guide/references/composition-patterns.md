# React Composition Patterns

Composition patterns for flexible, maintainable React 19 components. Covers compound components, state lifting, and internal composition as alternatives to boolean prop proliferation.

---

## 1. Component Architecture

**Impact: HIGH**

### 1.1 Avoid Boolean Prop Proliferation

**Impact: CRITICAL**

Boolean props like `isThread`, `isEditing`, `isDMThread` double possible states per flag and create exponential conditional logic. Composition patterns provide an alternative by extracting explicit variants.

**Incorrect: boolean props create exponential complexity**

```tsx
function Composer({
  onSubmit,
  isThread,
  channelId,
  isDMThread,
  dmId,
  isEditing,
  isForwarding,
}: Props) {
  return (
    <form>
      <Header />
      <Input />
      {isDMThread ? (
        <AlsoSendToDMField id={dmId} />
      ) : isThread ? (
        <AlsoSendToChannelField id={channelId} />
      ) : null}
      {isEditing ? (
        <EditActions />
      ) : isForwarding ? (
        <ForwardActions />
      ) : (
        <DefaultActions />
      )}
      <Footer onSubmit={onSubmit} />
    </form>
  )
}
```

**Correct: composition eliminates conditionals**

```tsx
function ChannelComposer() {
  return (
    <Composer.Frame>
      <Composer.Header />
      <Composer.Input />
      <Composer.Footer>
        <Composer.Attachments />
        <Composer.Formatting />
        <Composer.Emojis />
        <Composer.Submit />
      </Composer.Footer>
    </Composer.Frame>
  )
}

function ThreadComposer({ channelId }: { channelId: string }) {
  return (
    <Composer.Frame>
      <Composer.Header />
      <Composer.Input />
      <AlsoSendToChannelField id={channelId} />
      <Composer.Footer>
        <Composer.Formatting />
        <Composer.Emojis />
        <Composer.Submit />
      </Composer.Footer>
    </Composer.Frame>
  )
}

function EditComposer() {
  return (
    <Composer.Frame>
      <Composer.Input />
      <Composer.Footer>
        <Composer.Formatting />
        <Composer.Emojis />
        <Composer.CancelEdit />
        <Composer.SaveEdit />
      </Composer.Footer>
    </Composer.Frame>
  )
}
```

Each variant is explicit about what it renders. Share internals without sharing a single monolithic parent.

### 1.2 Use Compound Components

**Impact: HIGH**

Compound components structure complex UI with a shared context. Each subcomponent accesses shared state via context, not props.

**Incorrect: monolithic component with render props**

```tsx
function Composer({
  renderHeader,
  renderFooter,
  renderActions,
  showAttachments,
  showFormatting,
  showEmojis,
}: Props) {
  return (
    <form>
      {renderHeader?.()}
      <Input />
      {showAttachments && <Attachments />}
      {renderFooter ? (
        renderFooter()
      ) : (
        <Footer>
          {showFormatting && <Formatting />}
          {showEmojis && <Emojis />}
          {renderActions?.()}
        </Footer>
      )}
    </form>
  )
}
```

**Correct: compound components with shared context**

```tsx
const ComposerContext = createContext<ComposerContextValue | null>(null)

function ComposerProvider({ children, state, actions, meta }: ProviderProps) {
  return (
    <ComposerContext value={{ state, actions, meta }}>
      {children}
    </ComposerContext>
  )
}

function ComposerFrame({ children }: { children: React.ReactNode }) {
  return <form>{children}</form>
}

function ComposerInput() {
  const {
    state,
    actions: { update },
    meta: { inputRef },
  } = use(ComposerContext)
  return (
    <input
      ref={inputRef}
      value={state.input}
      onChange={(e) => update((s) => ({ ...s, input: e.target.value }))}
    />
  )
}

function ComposerSubmit() {
  const {
    actions: { submit },
  } = use(ComposerContext)
  return <button onClick={submit}>Send</button>
}

const Composer = {
  Provider: ComposerProvider,
  Frame: ComposerFrame,
  Input: ComposerInput,
  Submit: ComposerSubmit,
  Header: ComposerHeader,
  Footer: ComposerFooter,
  Attachments: ComposerAttachments,
  Formatting: ComposerFormatting,
  Emojis: ComposerEmojis,
}
```

**Usage:**

```tsx
<Composer.Provider state={state} actions={actions} meta={meta}>
  <Composer.Frame>
    <Composer.Header />
    <Composer.Input />
    <Composer.Footer>
      <Composer.Formatting />
      <Composer.Submit />
    </Composer.Footer>
  </Composer.Frame>
</Composer.Provider>
```

---

## 2. State Management

**Impact: MEDIUM**

### 2.1 Decouple State Management from UI

**Impact: MEDIUM**

The provider is the single location that manages state. UI components consume the context interface — agnostic to whether state comes from `useState`, Zustand, or a server sync.

**Incorrect: UI coupled to state implementation**

```tsx
function ChannelComposer({ channelId }: { channelId: string }) {
  const state = useGlobalChannelState(channelId)
  const { submit, updateInput } = useChannelSync(channelId)

  return (
    <Composer.Frame>
      <Composer.Input
        value={state.input}
        onChange={(text) => sync.updateInput(text)}
      />
      <Composer.Submit onPress={() => sync.submit()} />
    </Composer.Frame>
  )
}
```

**Correct: state management isolated in provider**

```tsx
function ChannelProvider({
  channelId,
  children,
}: {
  channelId: string
  children: React.ReactNode
}) {
  const { state, update, submit } = useGlobalChannel(channelId)
  const inputRef = useRef(null)

  return (
    <Composer.Provider
      state={state}
      actions={{ update, submit }}
      meta={{ inputRef }}
    >
      {children}
    </Composer.Provider>
  )
}

function ChannelComposer() {
  return (
    <Composer.Frame>
      <Composer.Header />
      <Composer.Input />
      <Composer.Footer>
        <Composer.Submit />
      </Composer.Footer>
    </Composer.Frame>
  )
}

function Channel({ channelId }: { channelId: string }) {
  return (
    <ChannelProvider channelId={channelId}>
      <ChannelComposer />
    </ChannelProvider>
  )
}
```

**Different providers, same UI:**

```tsx
// Local state for ephemeral forms
function ForwardMessageProvider({ children }) {
  const [state, setState] = useState(initialState)
  const forwardMessage = useForwardMessage()

  return (
    <Composer.Provider
      state={state}
      actions={{ update: setState, submit: forwardMessage }}
    >
      {children}
    </Composer.Provider>
  )
}

// Global synced state for channels
function ChannelProvider({ channelId, children }) {
  const { state, update, submit } = useGlobalChannel(channelId)

  return (
    <Composer.Provider state={state} actions={{ update, submit }}>
      {children}
    </Composer.Provider>
  )
}
```

### 2.2 Define Generic Context Interfaces for Dependency Injection

**Impact: HIGH**

A generic interface with `state`, `actions`, and `meta` enables any provider to implement it — the same UI components work with different state implementations.

**Core pattern:** Lifted state, composed internals, dependency-injectable state.

**Incorrect: UI coupled to specific state implementation**

```tsx
function ComposerInput() {
  const { input, setInput } = useChannelComposerState()
  return <input value={input} onChange={(e) => setInput(e.target.value)} />
}
```

**Correct: generic interface enables dependency injection**

```tsx
interface ComposerState {
  input: string
  attachments: Attachment[]
  isSubmitting: boolean
}

interface ComposerActions {
  update: (updater: (state: ComposerState) => ComposerState) => void
  submit: () => void
}

interface ComposerMeta {
  inputRef: React.RefObject<HTMLInputElement>
}

interface ComposerContextValue {
  state: ComposerState
  actions: ComposerActions
  meta: ComposerMeta
}

const ComposerContext = createContext<ComposerContextValue | null>(null)
```

**UI components consume the interface, not the implementation:**

```tsx
function ComposerInput() {
  const {
    state,
    actions: { update },
    meta,
  } = use(ComposerContext)

  return (
    <input
      ref={meta.inputRef}
      value={state.input}
      onChange={(e) => update((s) => ({ ...s, input: e.target.value }))}
    />
  )
}
```

**Different providers implement the same interface:**

```tsx
// Provider A: Local state for ephemeral forms
function ForwardMessageProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState(initialState)
  const inputRef = useRef(null)
  const submit = useForwardMessage()

  return (
    <ComposerContext
      value={{
        state,
        actions: { update: setState, submit },
        meta: { inputRef },
      }}
    >
      {children}
    </ComposerContext>
  )
}

// Provider B: Global synced state for channels
function ChannelProvider({ channelId, children }: Props) {
  const { state, update, submit } = useGlobalChannel(channelId)
  const inputRef = useRef(null)

  return (
    <ComposerContext
      value={{
        state,
        actions: { update, submit },
        meta: { inputRef },
      }}
    >
      {children}
    </ComposerContext>
  )
}
```

**Custom UI outside the component can access state and actions:**

```tsx
function ForwardMessageDialog() {
  return (
    <ForwardMessageProvider>
      <Dialog>
        <Composer.Frame>
          <Composer.Input placeholder="Add a message, if you'd like." />
          <Composer.Footer>
            <Composer.Formatting />
            <Composer.Emojis />
          </Composer.Footer>
        </Composer.Frame>

        <MessagePreview />

        <DialogActions>
          <CancelButton />
          <ForwardButton />
        </DialogActions>
      </Dialog>
    </ForwardMessageProvider>
  )
}

function ForwardButton() {
  const {
    actions: { submit },
  } = use(ComposerContext)
  return <button onClick={submit}>Forward</button>
}

function MessagePreview() {
  const { state } = use(ComposerContext)
  return <Preview message={state.input} attachments={state.attachments} />
}
```

The provider boundary is what matters — not the visual nesting. Components that need shared state just need to be within the provider.

### 2.3 Lift State into Provider Components

**Impact: HIGH**

Dedicated provider components hold state management. Sibling components outside the main UI access and modify state without prop drilling.

**Incorrect: state trapped inside component**

```tsx
function ForwardMessageComposer() {
  const [state, setState] = useState(initialState)
  const forwardMessage = useForwardMessage()

  return (
    <Composer.Frame>
      <Composer.Input />
      <Composer.Footer />
    </Composer.Frame>
  )
}

// Problem: How does this button access composer state?
function ForwardMessageDialog() {
  return (
    <Dialog>
      <ForwardMessageComposer />
      <MessagePreview /> {/* Needs composer state */}
      <DialogActions>
        <CancelButton />
        <ForwardButton /> {/* Needs to call submit */}
      </DialogActions>
    </Dialog>
  )
}
```

**Correct: state lifted to provider**

```tsx
function ForwardMessageProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState(initialState)
  const forwardMessage = useForwardMessage()
  const inputRef = useRef(null)

  return (
    <Composer.Provider
      state={state}
      actions={{ update: setState, submit: forwardMessage }}
      meta={{ inputRef }}
    >
      {children}
    </Composer.Provider>
  )
}

function ForwardMessageDialog() {
  return (
    <ForwardMessageProvider>
      <Dialog>
        <ForwardMessageComposer />
        <MessagePreview />
        <DialogActions>
          <CancelButton />
          <ForwardButton />
        </DialogActions>
      </Dialog>
    </ForwardMessageProvider>
  )
}

function ForwardButton() {
  const { actions } = use(Composer.Context)
  return <button onClick={actions.submit}>Forward</button>
}
```

**Key insight:** Components that need shared state don't have to be visually nested inside each other — they just need to be within the same provider.

---

## 3. Implementation Patterns

**Impact: MEDIUM**

### 3.1 Create Explicit Component Variants

**Impact: MEDIUM**

Explicit variant components replace a single component with many boolean props. Each variant composes the pieces it needs.

**Incorrect: one component, many modes**

```tsx
<Composer
  isThread
  isEditing={false}
  channelId='abc'
  showAttachments
  showFormatting={false}
/>
```

**Correct: explicit variants**

```tsx
<ThreadComposer channelId="abc" />
<EditMessageComposer messageId="xyz" />
<ForwardMessageComposer messageId="123" />
```

**Implementation:**

```tsx
function ThreadComposer({ channelId }: { channelId: string }) {
  return (
    <ThreadProvider channelId={channelId}>
      <Composer.Frame>
        <Composer.Input />
        <AlsoSendToChannelField channelId={channelId} />
        <Composer.Footer>
          <Composer.Formatting />
          <Composer.Emojis />
          <Composer.Submit />
        </Composer.Footer>
      </Composer.Frame>
    </ThreadProvider>
  )
}

function EditMessageComposer({ messageId }: { messageId: string }) {
  return (
    <EditMessageProvider messageId={messageId}>
      <Composer.Frame>
        <Composer.Input />
        <Composer.Footer>
          <Composer.Formatting />
          <Composer.Emojis />
          <Composer.CancelEdit />
          <Composer.SaveEdit />
        </Composer.Footer>
      </Composer.Frame>
    </EditMessageProvider>
  )
}
```

Each variant is explicit about what provider/state it uses, what UI elements it includes, and what actions are available.

### 3.2 Children vs Render Props

**Impact: MEDIUM**

`children` provides composition for static structure; `renderX` props are suited for cases where the parent passes data back to the child.

**Incorrect: render props**

```tsx
<Composer
  renderHeader={() => <CustomHeader />}
  renderFooter={() => (
    <>
      <Formatting />
      <Emojis />
    </>
  )}
  renderActions={() => <SubmitButton />}
/>
```

**Correct: compound components with children**

```tsx
<Composer.Frame>
  <CustomHeader />
  <Composer.Input />
  <Composer.Footer>
    <Composer.Formatting />
    <Composer.Emojis />
    <SubmitButton />
  </Composer.Footer>
</Composer.Frame>
```

**When render props are appropriate:**

```tsx
// Render props work well when you need to pass data back
<List
  data={items}
  renderItem={({ item, index }) => <Item item={item} index={index} />}
/>
```

Use render props when the parent needs to provide data to the child. Use children when composing static structure.

---

## 4. React 19 APIs

**Impact: MEDIUM**

### 4.1 React 19 API Changes

> **React 19+ only.** These patterns require React 19.

**ref is a regular prop (no forwardRef)**

```tsx
// ❌ Don't use forwardRef in React 19
const ComposerInput = forwardRef<HTMLInputElement, Props>((props, ref) => {
  return <input ref={ref} {...props} />
})

// ✅ ref as a regular prop
function ComposerInput({ ref, ...props }: Props & { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...props} />
}
```

**use() replaces useContext()**

```tsx
// ❌ Don't use useContext in React 19
const value = useContext(MyContext)

// ✅ use() — can also be called conditionally
const value = use(MyContext)
```

`use()` can also unwrap promises, enabling new data fetching patterns with Suspense:

```tsx
function DataDisplay({ dataPromise }: { dataPromise: Promise<Data> }) {
  const data = use(dataPromise)
  return <div>{data.content}</div>
}

function Page() {
  const dataPromise = fetchData()
  return (
    <Suspense fallback={<Skeleton />}>
      <DataDisplay dataPromise={dataPromise} />
    </Suspense>
  )
}
```

---

## References

1. [https://react.dev](https://react.dev)
2. [https://react.dev/learn/passing-data-deeply-with-context](https://react.dev/learn/passing-data-deeply-with-context)
3. [https://react.dev/reference/react/use](https://react.dev/reference/react/use)
