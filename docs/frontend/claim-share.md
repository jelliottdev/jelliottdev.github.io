# Standardized idea sharing

`claim-share.js` exposes `ClaimShare` in browsers and CommonJS exports in Node.
Load it after `claim-specification.js`. It makes no network requests and uses no
storage. Sharing is an explicit user action; tests use mocked native APIs.

## Link and import contract

`encode(confirmed)` returns `#idea=<base64url>`. `link(confirmed, baseURL)` clears
old query/fragment state and returns the same HTTP(S) page with that fragment.
This is a version-one JSON payload, limited to 12,000 decoded UTF-8 bytes and a
16,000-character full URL. Base64url is encoding, not encryption. The fields are
visible to anyone receiving the link. No server-side shortener or saved object
is created.

Only active standardized fields are included: canonical outcome and its exact
detail; ordered method steps and parameters; exact scope including holes and
passage descriptions; all rule states/values; and active unresolved semantic
constraints. Original prompt, materials, results, evidence, confirmation,
provenance and edit history are excluded. Per-step `sourceText` is excluded; for
any step lacking a label, its sole source wording is promoted to the
active label to avoid losing method meaning.

`decode(location.hash)` strictly checks version, allowed envelope/field keys,
field states, outcome IDs, base64url/UTF-8/JSON validity, unsafe keys, nesting and
size limits, then constructs a draft through `ClaimSpecification.createDraft`.
It returns:

```js
{draft, acknowledged: {aim:true, scope:true}, version:1}
```

The draft has a synthesized standardized summary as `source.text`,
`source.origin === 'shared_link'`, and `project_context` field provenance with a
`shared-link:v1` reference. It is never confirmed or executed. The recipient
must review the card. Unknown states remain unknown; acknowledgement lets the
UI avoid asking the same missing aim/scope questions on every opening. Import
must never automatically submit research. Malformed links should produce a
visible recoverable error, not fall back to interpreting their bytes as prose.

## Native share and image contract

```js
const png = await ClaimShare.prepare(confirmed); // before the share click
// prepare is an alias of renderPNG; both return a PNG Blob.
button.onclick = () => ClaimShare.share(confirmed, location.href, {
  preparedPNG: png
}).then(showShareFeedback);
```

`share` calls `navigator.share` synchronously before its first await, preserving
the click's transient user activation. A prepared image is attached only when
`navigator.canShare({files})` reports support and that Blob was generated for
the exact active payload. Otherwise native sharing receives title/text/link.
The module binds prepared images internally; an old card image cannot accompany
a newly edited card's URL. Render ahead after confirmation, and disregard any
completed render if the active snapshot changed.

The canvas draws a white/gray card with a serif heading and complete wrapped
standardized text. Common page scopes use exact compact ranges and passage
descriptions; rules have readable labels and methods retain their parameters.
Unknown rules have a concise collective label while the link retains every
exact state. A Liberpedia footer identifies the card. Layout measures every line and
grows the image. It refuses an excessive height rather than clipping or silently
dropping fields; the full link remains available. PNG pixels are not selectable;
the linked recipient card provides editable text. No DOM screenshot, remote
font, image, or media is loaded.

`renderPNG(spec,{document,maxHeight})` defaults to 1080 pixels wide and a maximum
height of 16,000 pixels. It rejects missing canvas support or PNG failures.
`share(spec,url,env)` accepts injectable `navigator`, `document`, `File` and
`preparedPNG` for tests. Return statuses:

- `shared`: native share completed, with `url` and optional `imageError`.
- `cancelled`: native `AbortError`, quiet; no clipboard/download side effects.
- `copied`: no native API; link copied, plus `png` when export succeeds.
- `fallback`: native or clipboard failure; `url`, optional `png`, and visible
  `error`/`imageError` for a manual copy/download UI.

The helper never clicks a download or opens a target application. Root UI owns
the explicit download button/object-URL lifecycle and visible fallback link.
For native failures, it returns immediately with any already prepared PNG;
without a prepared image, the UI may offer a separate `renderPNG` action.

## Verification

`node scripts/test_claim_share.cjs` checks active-only round trips, draft-only
import, exact holes/parameters/states, malformed versions/fields/bytes and size,
measured canvas wrapping/refusal, prepared-image binding, synchronous native
invocation, files/text fallback, cancellation and clipboard failure. Canvas,
native sharing and clipboard are mocked; no actual share/send or hosted call is
performed. Device share-target availability is a browser/OS capability, so these
tests do not claim an actual Discord handoff occurred.
