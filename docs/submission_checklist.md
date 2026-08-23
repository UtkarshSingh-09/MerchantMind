# 📋 MerchantMind — Submission Checklist

> Don't miss anything on September 5.

---

## Submission Requirements (from Razorpay)

- [ ] **Public GitHub repo** with working code
- [ ] **5-minute pitch video** (max)
- [ ] **Architecture documentation** (in repo)
- [ ] **Submit via Google Form**: https://forms.gle/d9r2gvxp8cmoZhon9

---

## GitHub Repo Checklist

- [ ] Repo is PUBLIC
- [ ] README.md with:
  - [ ] Project name and one-line description
  - [ ] Problem statement
  - [ ] Solution overview
  - [ ] Architecture diagram
  - [ ] Tech stack
  - [ ] Setup instructions (docker-compose up)
  - [ ] Demo video link
  - [ ] Screenshots
- [ ] `.env.example` (all vars, no real secrets)
- [ ] `docker-compose.yml` works with `docker-compose up`
- [ ] Architecture doc in `docs/`
- [ ] Clean commit history (no secrets committed)
- [ ] License file

## Demo Video Checklist

- [ ] Duration ≤ 5:00
- [ ] Shows the problem being solved
- [ ] Shows architecture (briefly)
- [ ] Shows WORKING demo:
  - [ ] Conversational checkout flow
  - [ ] Razorpay payment (test mode)
  - [ ] Upsell increasing order value
  - [ ] WhatsApp integration (if ready)
  - [ ] Audit trail
  - [ ] One failure handled gracefully
- [ ] Shows system design (Docker, CI/CD, multi-tenant)
- [ ] Clear audio narration
- [ ] No secrets visible on screen

## Technical Checklist

- [ ] Docker Compose starts all services
- [ ] CI/CD pipeline is green
- [ ] All API endpoints respond correctly
- [ ] Razorpay test payments work end-to-end
- [ ] Groq agent responds with relevant recommendations
- [ ] Audit trail captures all decisions
- [ ] Multi-merchant isolation verified
- [ ] At least basic tests pass

## Application Form

- [ ] Personal details filled
- [ ] Track selected: Track 01 — AI Growth & Agentic Commerce
- [ ] GitHub repo URL pasted
- [ ] Demo video URL pasted
- [ ] Submitted before September 5, 2026
