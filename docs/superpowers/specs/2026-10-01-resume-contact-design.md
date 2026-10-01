# Resume and Contact Page Design (E1)

- **Status:** approved for autonomous implementation
- **Date:** 2026-10-01
- **Scope:** one professional, printable `/resume/` page and a clearer public contact path. This is not a site redesign.

## 1. Objective

Add a concise public resume for recruiters, hiring managers, and technical collaborators. The page must make Dominic's experience, current focus, technical range, Montréal location, and preferred contact path easy to scan on screen and reliable to print.

The implementation will:

1. publish `/resume/` as semantic HTML in the existing Jekyll site;
2. render career history from `_data/timeline.yml`;
3. render technical capabilities from `_data/skills.yml`;
4. use LinkedIn as the only public contact channel;
5. expose a print control that calls the browser print dialog when JavaScript is available;
6. add a `Resume` header link while retaining the existing LinkedIn `Contact` link;
7. preserve the current visual language, layout shell, analytics, SEO, accessibility, and safe external-link attributes.

## 2. Audience and success criteria

The primary reader wants a quick, credible answer to three questions:

- What does Dominic do now?
- What experience and technical capabilities support that work?
- How can I contact him?

The page succeeds when a reader can understand those points in one scan, print the result without decorative site chrome, and reach the public LinkedIn profile without an email address, form, or third-party contact service.

## 3. Source material and content boundaries

Resume content must be grounded in existing public site material:

- the homepage title, description, About copy, current role, and Montréal location;
- `_data/timeline.yml` for every career entry;
- `_data/skills.yml` for every skill group and tag;
- the public profile links already present in the site layout and configuration.

The page may condense existing prose, but it must not invent employers, credentials, dates, achievements, email addresses, phone numbers, or claims. The career and skill values must not be copied into new YAML, front matter, JavaScript, or validation fixtures as a second content source.

## 4. Approaches considered

### 4.1 Recommended: dedicated Jekyll page using existing data directly

Create `resume/index.html` with the default layout and Liquid loops over `site.data.timeline` and `site.data.skills`. Add narrowly scoped `.resume-*` styles to the existing stylesheet and a small print action in the existing JavaScript.

**Advantages:** smallest coherent change, no new dependency, shared content remains authoritative, existing SEO/analytics/navigation behavior comes for free, and print output stays maintainable HTML.

**Trade-off:** the resume page has a little page-specific markup and CSS rather than a reusable resume component. That is appropriate while only one page needs it.

### 4.2 Separate resume layout

Create a dedicated layout that removes some global chrome and specializes metadata and scripts.

**Advantages:** complete control over the page shell and print output.

**Trade-off:** duplicates global SEO, analytics, accessibility, header, and footer behavior. It raises maintenance cost without a demonstrated second consumer.

### 4.3 Generated document or PDF

Generate a resume artifact from site data during the build.

**Advantages:** fixed-format download.

**Trade-off:** adds generation tooling, binary or artifact lifecycle concerns, and accessibility risks. It conflicts with the approved print-friendly HTML direction.

The design selects approach 4.1.

## 5. Information architecture

The page will use one visible `h1` and four compact content areas:

1. **Header:** name, current role, Montréal location, short professional summary, LinkedIn CTA, and print button.
2. **Experience:** complete career history from `_data/timeline.yml`, in the authored order.
3. **Technical capabilities:** complete skill groups from `_data/skills.yml`, in the authored order.
4. **Public profiles and contact:** LinkedIn as the prominent contact action, with GitHub, Kaggle, and Hugging Face as supporting public profiles.

The professional summary will reuse the substance of the existing homepage: Azure platforms for AI workloads, Databricks, infrastructure automation, IaC/CI/CD, MLOps/DataOps, and more than 25 years of systems experience. It will remain concise and will not repeat the full About section.

## 6. Rendering and data flow

`resume/index.html` will read directly from Jekyll data:

```text
_data/timeline.yml ──> site.data.timeline ──> experience list
_data/skills.yml   ──> site.data.skills   ──> capability groups
```

The page template will contain Liquid loops and escaped values. No intermediate resume data file will be added. Tests will compare the generated resume output with the loaded YAML so a template error, missing item, reordering, or duplicated hard-coded content fails validation.

The navigation contract will gain one internal item:

```yaml
- label: Resume
  href: /resume/
```

It will sit near the existing career-oriented links. The external `Contact` item remains a direct LinkedIn link with `target: _blank` and `rel: noopener`.

## 7. Visual and responsive behavior

The page will reuse existing colors, typography, button classes, borders, spacing scale, and content width. Resume-specific styles will:

- use a restrained document-like panel on the existing deep-space background;
- keep the summary readable at a moderate line length;
- present experience in a two-column year/content row on larger screens;
- collapse experience and action groups to one column on narrow screens;
- reuse the existing tag treatment for skill labels;
- avoid animation-dependent visibility so the resume is complete without JavaScript.

No homepage sections, global tokens, or unrelated components will be redesigned.

## 8. Print behavior

The print control will be a real `button` with an accessible label and a small `data-print-resume` hook. The existing site JavaScript will attach `window.print()` only when the button exists. Without JavaScript, the complete resume remains readable and the browser's normal print command still works.

An `@media print` block will:

- switch to black text on a white background;
- hide the navigation, footer, starfield, print/contact action controls, and other decorative elements;
- remove shadows, gradients, and panel borders that waste ink;
- retain visible destination URLs for public profile links where useful;
- avoid splitting experience and skill groups across pages when practical;
- use print-friendly spacing and type sizes.

No PDF will be generated or committed.

## 9. Accessibility and external-link safety

The page will preserve the global skip link and landmark structure from the default layout. It will add:

- one `h1` followed by ordered section headings;
- a descriptive introductory paragraph;
- semantic lists for experience, capabilities, and profile links;
- a keyboard-operable print button;
- visible focus styles inherited from the site;
- explicit link text such as `Contact on LinkedIn`, not ambiguous icon-only controls.

Every external profile link will use HTTPS, `target="_blank"`, and `rel="noopener"`. LinkedIn is the only contact method. No email address or form will appear in source or generated HTML.

## 10. SEO and analytics

The page will use front matter for a specific title, description, and keywords. The default layout will continue to provide canonical metadata, Open Graph metadata, Person JSON-LD, the GoatCounter script, site navigation, and footer links. The page will be included automatically in the generated sitemap.

No resume-specific analytics event or structured-data schema is required for E1.

## 11. Validation strategy

Implementation will follow test-driven development.

### Pre-build checks

Focused Python tests will verify:

- the navigation data includes the internal Resume link and preserves the safe LinkedIn Contact link;
- the resume template loops over both shared data sources;
- timeline and skill values are not duplicated as hard-coded page content;
- the page has expected headings, semantic structure, accessible controls, LinkedIn CTA, profile-link safety, and print hooks;
- CSS includes scoped responsive and print rules;
- JavaScript connects the print button to `window.print()`.

The existing data validator remains the pre-build source-contract check. It will be updated only for the approved navigation item.

### Post-build checks

The generated-output checker will validate `_site/resume/index.html` and compare rendered experience and skill collections with `_data/timeline.yml` and `_data/skills.yml`. It will also enforce the LinkedIn-only contact behavior, print control, basic heading structure, and safe external-link attributes.

CI will add `_site/resume/index.html` to the existing required-output list and run the extended checker after the Jekyll build. This reuses current tooling and adds protection at the point where Liquid output can be inspected.

## 12. Documentation

`README.md` will document:

- `/resume/` as a generated site page;
- `_data/timeline.yml` and `_data/skills.yml` as the resume's content owners;
- the print-friendly HTML behavior;
- LinkedIn as the intentional public contact route.

## 13. Non-goals

- A broader visual redesign.
- A downloadable or committed PDF.
- An email address, phone number, contact form, or contact service.
- New resume-specific YAML that duplicates skills or timeline entries.
- New claims, employers, education details, certifications, or accomplishments.
- Changes to `/now/` (E3) or general finishing work (E4).
- Reworking the homepage, global footer, analytics, or navigation behavior beyond the one Resume link.

## 14. Acceptance criteria

E1 is complete when:

- `/resume/` builds to `_site/resume/index.html`;
- the generated page renders every timeline entry and skill group from the shared YAML in source order;
- no timeline or skill values are maintained separately in the resume template;
- the page clearly identifies Dominic's current role and Montréal location using existing site copy;
- LinkedIn is the only contact method and all external links are safe;
- the header navigation contains both `Resume` and the existing LinkedIn `Contact` link;
- the page is responsive, keyboard accessible, readable without JavaScript, and print-friendly;
- focused tests, the full Python suite, relevant Node tests, the Ruby 3.4 Jekyll build, generated-output checks, and `git diff --check` pass;
- README and CI accurately describe and protect the new page.
