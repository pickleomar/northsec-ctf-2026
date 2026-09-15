# Frontend for Escape-The-Matrix

This directory contains the React/Vite frontend for the CTF challenge.

## Observing DOM ID Changes

A core part of this challenge involves observing how the DOM mutates after each successful step of the GIF sequence.

To see the changes:

1.  Open your browser's Developer Tools (usually by pressing F12 or right-clicking and selecting "Inspect").
2.  Go to the "Elements" or "Inspector" tab.
3.  Locate the `div` with the `id` that starts with `matrix-card`. It will look something like this:
    ```html
    <div id="matrix-card" class="card" data-testid="matrix-card-div">
      ...
    </div>
    ```
4.  Click the "Escape Matrix" button on the web page.
5.  Watch the `id` of that `div` in the Elements tab. After each click, a new URL-safe Base64 fragment will be appended to the id, separated by a dot.

    **After 1st click:**
    ```html
    <div id="matrix-card.someFragment" ...>
    ```

    **After 2nd click:**
    ```html
    <div id="matrix-card.someFragment.anotherFragment" ...>
    ```

By collecting these fragments in order, you can reconstruct the final message as described in the `server/CTF-API.md` guide.