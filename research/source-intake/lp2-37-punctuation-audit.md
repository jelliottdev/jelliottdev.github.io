# LP2-37 numbered-item punctuation: image audit

The supplied discussion asked whether item **2** lacks the closing mark visible after later items, perhaps to preserve layout. The first part is visible; the proposed reason is not established.

| Item | Where its text ends | What the archived JPEG shows | Reviewed text |
| --- | --- | --- | --- |
| 2 | LP2-37, line 4 | Last rune pair, then white space. No terminal three-dot cluster. | Correctly omits the final `.`. The older raw transcript includes one; its reviewed correction removes it. |
| 3 | LP2-37, line 9 | A terminal three-dot cluster after the last rune. | Retains `.` as its one-character transcription convention. |
| 4 | LP2-38, line 3, after crossing the page break | The same terminal three-dot cluster. | Retains `.`. |

The marks transcribed as `.` here are three-dot end marks in the image, distinct from the single word-separation dots. Item 4 continues across the LP2-37/38 page boundary; the end of LP2-37 is **not** its sentence end. The missing mark after item 2 does not change the rune-only stream. The image leaves substantial white space to the right of item 2's final rune, so a simple lack-of-horizontal-room explanation is not supported by the visible layout. The image alone cannot establish why the mark was omitted.

Pixel-exact, unscaled crops from the pinned 2400 × 3600 JPEGs:

![Item 2 final runes with no terminal three-dot mark](lp2-37-item2-ending.png)

![Item 3 final runes followed by three-dot mark](lp2-37-item3-ending.png)

![Item 4 final runes followed by three-dot mark on the following page](lp2-38-item4-ending.png)

The crop rectangles, in `(left, top, right, bottom)` original-image pixels, are respectively `(1510, 1210, 2020, 1390)`, `(510, 2260, 1150, 2470)`, and `(900, 1020, 1560, 1230)`. They were saved as PNG without resizing or enhancing the source pixels. The full carriers and text records are [LP2-37](../../images/lp2-37.jpg), [LP2-38](../../images/lp2-38.jpg), [LP2-37 page data](../../data/pages/lp2-37.json), and [LP2-38 page data](../../data/pages/lp2-38.json).

SHA-256: LP2-37 JPEG `cee96d7e71b7de4d4e57237faacefad791229c153202e8224e4bedda45fb8f43`; LP2-38 JPEG `aec1898f599f57265d6422f3082a481db94a27f62230affbadee595d05077f8c`. The three crops hash to `ae1e2ad281ba9db791afcbc64a79fae8f62701cd259fb6dbbbd6813b8812c734`, `bc715a2d3b0ecb6ca336a7eea5aaefefb27121e77642c3d9bf4b6ee4a5d89f2a`, and `5f720036d20a01ee191701644b9ae0d45c45dcb03a4534b8c65877039d3ddf28` in table order.
