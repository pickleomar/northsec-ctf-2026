# ColdTap

Sponsors at a conference received NFC hardware wallet badges that were supposed to prove booth attendance and unlock swag on-chain.

A sponsor claims one badge was "air-gapped enough" because the key never leaves the card.

You have:

- a raw Cortex-M firmware flash image for the badge wallet
- several hallway NFC tap captures collected around the same booth
- the `SponsorVault` contract source
- a small instance metadata file

Your goal is to recover the badge wallet secret material well enough to decrypt the offline flag blob.

Flag format: `NSC{...}`

Hint: `Air-gapped is not field-gapped.`
