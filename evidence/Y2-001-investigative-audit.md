# Julie promo-field investigative audit

**Read-only investigation completed October 26, 2026.** The field was not newly removed after the CEO requested complimentary access. It was hidden on September 23 during a mobile checkout presentation change; the October 25 guest-access implementation then attached working code logic to that already-hidden field without restoring its visibility. The two relevant commits establish this sequence directly ([original hiding change](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820), [guest-access implementation](https://github.com/Longevity-Academy/julie-masterclass/commit/b298f834629604d3039b4959fcbb9ca688ef0183)).

## Executive verdict

- **What happened:** A CSS rule hid the promo label and the entire input/button container using `display:none!important`; the form elements were not deleted ([original diff](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820)).
- **When:** The change was committed September 23 at 11:09:53 Israel time, and its GitHub Pages deployment job completed at 11:10:44 Israel time ([commit](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820), [successful deployment](https://github.com/Longevity-Academy/julie-masterclass/actions/runs/35835582664)).
- **Recorded purpose:** The commit was titled “Keep selected checkout session fully readable on mobile,” but it supplied no explanation for hiding the promo field ([commit and full diff](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820)).
- **Tracking explanation:** No evidence retrieved establishes either an actual tracking problem caused by this field or an explicit decision to hide it because of an assumed tracking problem; the originating diff changes presentation, while the later tracking-related checkout commit merely retains the hiding rule ([originating diff](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820), [later checkout diff](https://github.com/Longevity-Academy/julie-masterclass/commit/f4407af255fafebae33f98c33495477bf41a6420)).
- **Why the guest launch failed:** The October 25 implementation explicitly relied on the existing promo field but changed only the guest JavaScript and its script inclusion, not the CSS hiding that field ([guest-access diff](https://github.com/Longevity-Academy/julie-masterclass/commit/b298f834629604d3039b4959fcbb9ca688ef0183)).

The defensible classification is **an undocumented UI suppression followed by a guest-feature integration and acceptance-testing failure**. It is not established as a necessary tracking protection, a user-authorized cancellation of the guest benefit, or a newly introduced removal of [confidential guest code].

## Timeline and chain of evidence

Times below distinguish source changes from deployment completion. September timestamps use Israel daylight time, UTC+3; October 25–26 timestamps use Israel standard time, UTC+2.

| Israel date and time | UTC time | Event and evidence |
|---|---|---|
| September 23, 11:09:53 | September 23, 08:09:53 | Commit `9d986ab` first adds the combined date/promo hiding selector while implementing a mobile-readable selected-session summary ([commit](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820)). |
| September 23, 11:10:44 | September 23, 08:10:44 | The deployment job for `9d986ab` finishes successfully; this is the deployment record, not a claim about every visitor's browser-cache refresh time ([Pages workflow](https://github.com/Longevity-Academy/julie-masterclass/actions/runs/35835582664)). |
| September 24, 01:42:18 | September 23, 22:42:18 | Commit `f4407af` restores the date selector but leaves the promo label and container hidden; its wider work concerns CRM cart-stage events, order timing, quote validation and payment validation ([commit](https://github.com/Longevity-Academy/julie-masterclass/commit/f4407af255fafebae33f98c33495477bf41a6420)). |
| October 25, 11:47:37 | October 25, 09:47:37 | Commit `b298f83` introduces the confidential, hashed guest-access handler through the existing promo field; no visibility fix is included ([commit](https://github.com/Longevity-Academy/julie-masterclass/commit/b298f834629604d3039b4959fcbb9ca688ef0183), [successful release](https://github.com/Longevity-Academy/julie-masterclass/actions/runs/40182114361)). |
| October 25, 11:51:13 | October 25, 09:51:13 | Commit `20b960f` rotates only the accepted code hash; it does not change CSS or form visibility ([commit](https://github.com/Longevity-Academy/julie-masterclass/commit/20b960fa5288860960bd99c068f4a7a9b73a9cbb)). |
| October 25, 11:52:16 | October 25, 09:52:16 | The deployment job for `20b960f` completes successfully with the hidden-field condition still present in the released source ([deployment](https://github.com/Longevity-Academy/julie-masterclass/actions/runs/40182362876)). |
| October 26, 12:00:52 | October 26, 10:00:52 | Commit `f72201e` restores the field and label display and versions the stylesheet reference; it does not change payment, tracking or guest-handler JavaScript ([repair](https://github.com/Longevity-Academy/julie-masterclass/commit/f72201e248b9328a52ea961fa2a9b184e3e24225)). |
| October 26, 12:02:01 | October 26, 10:02:01 | Commit `1ef760d` restores the generic “I have promo code” label after the emergency repair temporarily used “Promo / guest code” ([label correction](https://github.com/Longevity-Academy/julie-masterclass/commit/1ef760dc70224e97fe39b6cb13ccc1dba2e6fae2)). |

## How it was hidden

The September 23 change added this global rule, outside a mobile-only media query ([original CSS diff](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820)):

```css
#emDate,[for="emPromo"],#enrollModal .em-promo {
  display: none !important;
}
```

It hid three things together: the selected-date element, the promo label, and the container holding the promo input and Apply button. The same commit added a readable date-summary paragraph, explaining the date-related part of the change but not why promo redemption was also suppressed ([full diff](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820)).

The subsequent checkout update removed the date element from that rule but preserved the other two selectors. This left the following exact blocking rule in production ([follow-up diff](https://github.com/Longevity-Academy/julie-masterclass/commit/f4407af255fafebae33f98c33495477bf41a6420)):

```css
[for="emPromo"],#enrollModal .em-promo {
  display: none !important;
}
```

This was not a guest-code expiry, invalid-code response, payment-provider limitation, or a missing HTML input. It was a rendering rule that made the existing redemption controls unavailable to ordinary visitors ([CSS repair diff showing the retained input and replaced hiding rule](https://github.com/Longevity-Academy/julie-masterclass/commit/f72201e248b9328a52ea961fa2a9b184e3e24225)).

## Why: what is proven and what remains unknown

### Original September decision

The recorded change concerns mobile date readability; neither its commit message nor the inspected diff states a business or tracking rationale for hiding the promo controls. The subsequent checkout commit also provides no explanation for preserving that suppression ([September 23 change](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820), [follow-up change](https://github.com/Longevity-Academy/julie-masterclass/commit/f4407af255fafebae33f98c33495477bf41a6420)).

There is relevant context, but it is not proof of motive: before the hiding change, the old Apply handler merely displayed “Not valid for this package” for any nonempty code. Removing an inactive control during UI cleanup is therefore a plausible explanation, but no retrieved instruction or rationale confirms it ([pre-change checkout source](https://raw.githubusercontent.com/Longevity-Academy/julie-masterclass/b0930cce257d48ee00d0533812812dc8091a5950/index.html)).

**The exact subjective reason for adding the promo selectors is undocumented in the recovered evidence.** It would be inaccurate to invent a tracking rationale, claim the CEO requested this suppression, or claim we have recovered the original implementer's private reasoning.

### October guest rollout

The guest implementation states that it uses the existing “I have promo code” field and installs an event handler for its Apply button. Its diff adds the guest script and one script tag, leaving the old hiding CSS untouched ([guest implementation](https://github.com/Longevity-Academy/julie-masterclass/commit/b298f834629604d3039b4959fcbb9ca688ef0183)).

The recovered October 25 conversation separately establishes the intended requirement: a 100% invitation for the CEO's contacts, confidential rather than publicly advertised, followed by an explicit request to use [confidential guest code] and confirmation that Standard and VIP were covered. The assistant replied that the code was checked and worked through the promo field; those are statements in the original conversation, not proof that a real guest could reach the field.

The distinction matters: **keeping the code secret did not require hiding the redemption input.** The October implementation failed to reconcile the new guest behavior with an old presentation rule, and the assurance supplied afterward did not establish successful ordinary-user access.

The available records do not reveal whether the earlier test was programmatic, isolated, performed on another version, or simply insufficient. They do establish that the production source released with the guest feature still hid the very controls the feature required ([guest release diff](https://github.com/Longevity-Academy/julie-masterclass/commit/b298f834629604d3039b4959fcbb9ca688ef0183), [subsequent visibility repair](https://github.com/Longevity-Academy/julie-masterclass/commit/f72201e248b9328a52ea961fa2a9b184e3e24225)).

## Tracking investigation

- **Was a tracking defect demonstrated?** No supporting defect report, before/after measurement, or rationale for this hiding rule was found in the inspected commits and original conversation records; the original change is a presentation change, not a tracking implementation ([originating diff](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820)).
- **Was there an explicit assumption that the field hurt tracking?** None was found; the later commit's tracking-related title does not establish causation because its diff shows that the hiding rule already existed ([later checkout diff](https://github.com/Longevity-Academy/julie-masterclass/commit/f4407af255fafebae33f98c33495477bf41a6420)).
- **Is visibility used as a tracking guard?** The inspected live Meta tracking script does not reference `emPromo` or `.em-promo`; its Purchase guard instead requires an order ID, a finite positive value and a three-letter currency, and rejects an already-confirmed order ([live tracking implementation](https://www.longevitylifeacademy.com/julie-masterclass/assets/julie-meta-tracking.js)).
- **What does the guest handler do?** It intercepts the valid-code branch before the normal payment flow, calls the existing CRM submission API, displays the guest confirmation, and sends a distinct `LGV_Guest_Access_Registered` lifecycle event; it contains no direct Meta Purchase call ([guest handler](https://github.com/Longevity-Academy/julie-masterclass/commit/b298f834629604d3039b4959fcbb9ca688ef0183)).
- **Was “no Meta events” too broad?** Yes as a blanket description of the entire guest visit: PageView and ViewContent have independent page-level paths, so the guest handler's lack of purchase-tracking calls does not mean the whole page emits no Meta events ([page-level tracking code](https://www.longevitylifeacademy.com/julie-masterclass/assets/julie-meta-tracking.js)).
- **Did the visibility repair alter tracking code?** No; the repair and label follow-up affect CSS and HTML presentation, not JavaScript tracking, payment or guest-handler files ([repair](https://github.com/Longevity-Academy/julie-masterclass/commit/f72201e248b9328a52ea961fa2a9b184e3e24225), [follow-up](https://github.com/Longevity-Academy/julie-masterclass/commit/1ef760dc70224e97fe39b6cb13ccc1dba2e6fae2)).

This supports a narrow conclusion: **there is no demonstrated tracking justification for hiding the input.** It does not certify every downstream CRM automation, actual Meta attribution outcome, or guest enrollment.

## Responsibility and verification failure

The relevant commits are attributed to the `gitteromri-ux` Git identity. That identifies the account used to publish them, not proof that Omri personally wrote or requested the hiding rule ([originating commit](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820), [guest implementation commit](https://github.com/Longevity-Academy/julie-masterclass/commit/b298f834629604d3039b4959fcbb9ca688ef0183)).

The preserved guest-rollout conversation attributes the implementation and “checked” assurance to the assistant. The operational failure is therefore in the assistant-delivered integration and its acceptance claim: functional code was treated as sufficient without establishing that the production visitor could access it.

Two separate failures must not be collapsed into one:

- **Original change control:** Promo redemption was suppressed in a mobile date-presentation change without a documented promo-specific rationale ([September change](https://github.com/Longevity-Academy/julie-masterclass/commit/9d986ab7ce14f897bdc7cf20c861e4236cbb9820)).
- **Later feature acceptance:** New guest logic was attached to an existing element without repairing its known-in-source hidden state ([October guest diff](https://github.com/Longevity-Academy/julie-masterclass/commit/b298f834629604d3039b4959fcbb9ca688ef0183)).

## Audit performed and limitations

This investigation used full Git history, parent/current source comparisons, GitHub Actions deployment records, the original September checkout conversation and its release report, and the October guest-code conversation. No production edits, payments, CRM orders, external messages or campaign changes were made during this investigative turn.

The following checks were executed:

- **Historical CSS reproduction:** In a read-only browser session, temporary client-local substitution of the September rules made both the label and container compute to `display:none`; restoring current CSS returned `block` and `flex`.
- **Sixteen automated checks:** Read-only Git assertions and isolated Node simulations passed for both Standard and VIP, including code acceptance, zero-dollar presentation, mocked CRM registration, and no Meta calls from the guest handler itself.
- **Scope of simulation:** CRM and lifecycle calls were mocked; these results do not establish actual enrollment, receipt delivery, Zoom access, server-side attribution, or full-page event behavior.
- **Impact count:** Thirty affected people is Omri's reported impact, not a visitor count independently established from session logs.
- **Historical certainty:** Commit and deployment times are known; individual visitors' cache states and every historical session are not.

## Recommended prevention, not implemented in this audit

The appropriate release requirement is an ordinary-browser journey: reach the promo field without DOM manipulation, apply a valid code, verify both tiers and dates, reject invalid/expired codes, and prove backend fulfillment in an approved non-production test environment. Paid-flow regression checks must separately establish that normal checkout remains intact and that complimentary registration is not counted as paid revenue.

A release should fail if the input or its label/container is hidden, even when a programmatic code test passes. “Code accepted,” “registration request accepted,” “actual access granted,” and “paid attribution verified” must be reported as separate outcomes rather than one claim of “working.”
