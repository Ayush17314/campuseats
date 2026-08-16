# Network Analysis — DevTools Walkthrough

**Site analyzed:** https://www.crunchyroll.com/discover
**Tool used:** Chrome DevTools → Network panel, "Disable cache" ticked, page reloaded


## Results

| Metric|Value|
|---|---|
|Total number of requests|307|
|Total transferred size|8.2 MB transferred / 13.9 MB resources (uncompressed)|
|DOMContentLoaded|517 ms|
|Full page Load|1.12 s|
|Slowest single resource| file name:ketch-sdk.js type: script — time 1.54s|
|Why it was slowest| Third-party script (ketchjs.com — a consent/cookie-management SDK), loaded from an external CDN, not part of the page's own content|
|3xx responses seen|One 301 redirect on 512.png (76 ms)|
|4xx responses seen|None observed|

## What the waterfall shows

The page itself loads fast — DOMContentLoaded at 517 ms and the visible page ready
at 1.12 s — but the "Finish" time of 2.4 minutes shows the browser kept making
requests long after the page was usable. With 279 total requests, most of the extra
time comes from background scripts: analytics, ads, and third-party trackers
(like ketch-sdk.js) that keep loading even after the user can already interact with
the page. This is a common pattern on media/streaming sites — the core content loads
quickly, but tracking and consent-management scripts trail on far longer.

## Note on the two size numbers

Chrome reports 8.2 MB transferred vs 13.9 MB resources. The first is what actually
crossed the network after compression (gzip/br); the second is the real size once
the browser decompresses it. The gap shows the server is compressing responses
before sending them — tied to the Content-Encoding header from Tutorial 1.

## Note on the redirect (301)

512.png returned a 301 (Moved Permanently) rather than the image directly — likely
an image CDN redirecting to a versioned or region-specific URL. A 301 means the
browser has to make a second request to actually fetch the resource, adding a small
amount of extra latency (76 ms here) for that one asset.