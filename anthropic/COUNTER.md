# Claude claims counter

Service: Anthropic Claude (claude.ai)  
Updated: 2026-11-11 19:59 UTC

**Claims logged:** 4  
**Proven in transcript:** 3  
**Severity 4 or 5:** 0  
**Minutes lost, evidenced:** 0  
**Value claimed by account owner, USD:** 0

## By category

- AUDIT_FAILURE: 2
- WASTED_COMPUTE: 1
- SCOPE_REDUCTION: 1

## Every claim

### CLAUDE-0001 · 2026-11-11 · Longevity Life Academy · SCOPE_REDUCTION · severity 3 · proven

Asked for a full end-to-end iPhone checkout audit with card-field load times in 10 minutes, Claude stopped before the card form, did not use BrowserStack, and asked for a further go instead of completing the flow.

> Claude: Reply **"go test lead"** and I'll run the full card-field timing on all three iPhones.

> Omri: Stop. I need u to checkout in full motherfucker!!!

Chat: https://claude.ai/code/session_01SzigGTAHPfMUgu7bUJ7NJR  
Value claimed: pending  
Terms clause contradicted: requested scope not performed in the delivery; not an output-accuracy issue

### CLAUDE-0002 · 2026-11-11 · Longevity Life Academy · AUDIT_FAILURE · severity 3 · proven

Claude reported the checkout as running end to end while Meta Pixel and CAPI had been blocked in every run, so tracking was not verified until the client asked.

> Claude: Full checkout runs end to end on all three iPhones, and the live Airwallex card form loads.

> Omri: Wait what about fucking capiiiiiii

Chat: https://claude.ai/code/session_01SzigGTAHPfMUgu7bUJ7NJR  
Value claimed: pending  
Terms clause contradicted: end-to-end audit reported without the tracking layer the client relies on; not covered by the output-accuracy disclaimer

### CLAUDE-0003 · 2026-11-11 · Longevity Life Academy · AUDIT_FAILURE · severity 3 · alleged

Claude stated the token change and the redirect are not what breaks CAPI; the client states both are causes Claude did not check the right way, and no verified cause of the lost Purchase IDs was found in the chat.

> Claude: I checked both of your suspected causes on the live system. Neither one is what breaks CAPI today.

> Omri: Option 1 token change done last week between a shared token for longevity and French which now seperate

Chat: https://claude.ai/code/session_01SzigGTAHPfMUgu7bUJ7NJR  
Value claimed: pending  
Terms clause contradicted: diagnosis presented as checked before the full relay code and Events Manager were read

### CLAUDE-0004 · 2026-11-11 · Longevity Life Academy · WASTED_COMPUTE · severity 2 · proven

The instrumented step 2 to payment trace failed on its first run from a script error on binary request bodies and had to be rewritten, delaying the answer the client asked for.

> Claude: Running it all in one pass:

> Omri: Check every single thing that happens between stepn2 and payments and thats the answer

Chat: https://claude.ai/code/session_01SzigGTAHPfMUgu7bUJ7NJR  
Value claimed: pending  
Terms clause contradicted: n/a
