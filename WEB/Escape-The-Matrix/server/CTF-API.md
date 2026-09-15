# Escape The Matrix - API Guide

This document outlines the API for the "Escape The Matrix" challenge and explains how to reconstruct the final flag/instruction.

## Endpoint

The only interactive endpoint is:

- **URL:** `/api/m4tr1x_Esc4p3d/enT3r_th3_v0iD`
- **Method:** `POST`
- **Content-Type:** `application/json`

### Request Body

The server accepts a JSON body with the following structure. For this challenge, only the `signal` field is processed by a logger.

```json
{
  "signal": "your-value",
  "trace": "...",
  "entropy": "...",
  "node": "..."
}
```

## GIF Sequence and Fragment Collection

The core of the challenge is to obtain a sequence of GIFs, each of which is accompanied by a fragment of a larger message. These fragments are delivered via an HTTP response header.

### Response

- **On Success (200 OK):**
  - **Content-Type:** `image/gif`
  - **Body:** The binary data of the GIF for the current step.
  - **Header:** `X-Matrix-Id` - A Base64-encoded string representing one fragment of the final message.

- **On Error:**
  - `429 Too Many Requests`: If you make requests less than 1 second apart.
  - `410 Gone`: If you have already completed the entire sequence.

## Reconstructing the Final Instruction

To solve the challenge, you must collect all fragments in the correct order and decode them.

### Step-by-Step Guide

1.  **Initiate Sequence:** Make your first `POST` request to the endpoint. The response will contain the first GIF and the first fragment in the `X-Matrix-Id` header.

2.  **Inspect the Frontend (Optional but Recommended):** The frontend automatically processes these fragments. After each button click, inspect the `div` element with an `id` that starts with `matrix-card`. You will see the `id` being appended with URL-safe versions of the fragments, like so: `matrix-card.fragment1.fragment2`.

3.  **Collect Fragments:** Repeat the request process. Each request will yield the next GIF and the next fragment. The server maintains your progress using your session cookie. Store each Base64 fragment from the `X-Matrix-Id` header in order.

4.  **Concatenate and Decode:** Once you have collected all the fragments, you have a series of Base64 strings. The frontend converts them to a URL-safe format for the DOM `id`. The original fragments from the `X-Matrix-Id` header are standard Base64.

    Let's say you collected these fragments from the headers:
    - `dGVzdA==`
    - `YW5k`
    - `MQ==`

    Simply concatenate them:
    `dGVzdA==YW5kMQ==`

    This example is for illustration. The actual fragments will be different.

5.  **Final Decode:** Take the final concatenated Base64 string and decode it. This will reveal the hidden instruction required to capture the flag.

    For example, using an online tool or a command-line utility:
    ```bash
    echo "your-concatenated-base64-string" | base64 --decode
    ```

The decoded output will be a human-readable instruction, likely an HTTP request you need to make to get the final flag.
