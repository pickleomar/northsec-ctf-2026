# BUZZK1LL
## **Author:** BlackMy7h
 

### Category: Reverse Engineering / Web

## Player Brief

Open the challenge URL in a browser and recover the real flag.

What you should expect:

- The page looks like a mosquito-swatting arcade game.
- A visible score and badge system exist, but they are not the real objective.
- All important logic is shipped to the browser.
- Browser developer tools and client-side reversing are in scope.
- The flag format is `NSC{...}`.

Suggested player workflow:

1. Open the challenge and interact with it normally.
2. If the visible win condition looks suspicious, inspect the client assets loaded by the page.
3. Reverse the JavaScript and the WebAssembly module to find the real verification path.
4. Trigger the hidden success condition and submit the revealed flag.

## Infra Deployment

The bundle is prepared for a dynamic-flag deployment flow.

At container startup, the service generates `public/game.js` and `public/game.wasm`
from internal templates using `FLAG`.

## Local Deployment

Build and run the container:

```sh
docker build -t buzzk1ll .
docker run --rm -p 8080:31337 -e FLAG='NSC{test_flag}' buzzk1ll
```

Then open:

```text
http://127.0.0.1:8080/
```
