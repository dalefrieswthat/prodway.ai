import StatsSection from './components/StatsSection';

export default function Home() {
  return (
    <main className="min-h-screen grid-bg font-sans antialiased">
      {/* Navigation — clean, minimal */}
      <nav className="fixed top-0 w-full z-50 border-b border-[#262626] bg-[#050505]/90 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-green-500/12 flex items-center justify-center">
              <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="font-semibold text-[17px] text-[#fafafa] tracking-tight">Prodway</span>
          </div>
          <a
            href="mailto:dale@prodway.ai"
            className="px-4 py-2.5 text-[15px] font-medium border border-[#262626] rounded-lg text-[#fafafa] hover:border-green-500/40 hover:bg-green-500/10 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[#050505] transition-colors duration-200"
          >
            Get Early Access
          </a>
        </div>
      </nav>

      {/* Hero — one clear value prop */}
      <section className="pt-28 md:pt-36 pb-16 md:pb-24 px-5">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 mb-6 text-[13px] font-medium border border-green-500/35 rounded-full text-green-500 bg-green-500/10">
            <svg className="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Now in Private Beta
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-[#fafafa] mb-5 leading-[1.1]">
            Scale your agency
            <br />
            <span className="gradient-text">without hiring</span>
          </h1>

          <p className="text-lg md:text-xl text-[#a3a3a3] max-w-xl mx-auto mb-4 leading-relaxed">
            AI tools that handle the boring parts—proposals, contracts, invoicing—so you can focus on the work that matters.
          </p>
          <p className="text-base md:text-lg text-[#717171] max-w-xl mx-auto mb-10 leading-relaxed">
            We&apos;re the company-data layer for forms and SOWs; we get better as more teams use us.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="mailto:dale@prodway.ai"
              className="inline-flex items-center justify-center gap-2 min-h-[48px] px-6 py-3 bg-green-500 text-[#050505] font-semibold text-[15px] rounded-lg hover:bg-[#16a34a] focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[#050505] transition-colors duration-200"
            >
              Request Access
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </a>
            <a
              href="#products"
              className="inline-flex items-center justify-center min-h-[48px] px-6 py-3 border border-[#262626] rounded-lg text-[#fafafa] font-medium text-[15px] hover:bg-white/5 hover:border-[#404040] focus:outline-none focus:ring-2 focus:ring-[#525252] focus:ring-offset-2 focus:ring-offset-[#050505] transition-colors duration-200"
            >
              See products
            </a>
          </div>
        </div>
      </section>

      {/* Stats — live counts + value props */}
      <StatsSection />

      {/* Products Section — YC/Airbnb quality */}
      <section id="products" className="py-20 md:py-28 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-[#fafafa] mb-3">
              Two products. One mission.
            </h2>
            <p className="text-[#a3a3a3] text-base md:text-lg max-w-xl mx-auto">
              Eliminate busywork from your consulting business.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 md:gap-8">
            {/* SowFlow Card */}
            <div className="group bg-[#0c0c0c] border border-[#262626] rounded-xl p-7 md:p-8 shadow-[0_1px_3px_rgba(0,0,0,0.3)] hover:border-green-500/25 hover:shadow-[0_4px_20px_rgba(0,0,0,0.4)] transition-all duration-200 ease-out">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="min-w-0">
                  <h3 className="text-xl font-bold tracking-tight text-[#fafafa]">SowFlow</h3>
                  <span className="inline-block mt-1 px-2.5 py-0.5 text-xs font-medium bg-green-500/12 text-green-500 rounded-full">
                    Live
                  </span>
                </div>
              </div>

              <p className="text-[#e5e5e5] text-[15px] leading-relaxed mb-5">
                Generate professional SOWs from a single Slack command. Send for signature. Invoice automatically.
              </p>

              <a
                href="https://dynamic-transformation-production.up.railway.app/slack/install"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2.5 w-full min-h-[48px] py-3 px-4 mb-5 rounded-lg bg-green-500 text-[#050505] font-semibold text-[15px] hover:bg-[#16a34a] focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[#050505] transition-colors duration-200"
              >
                <img src="/sowflow-icon.png" alt="" className="w-5 h-5 rounded object-contain" width={20} height={20} />
                Add to Slack
              </a>

              <div className="bg-[#141414] border border-[#262626] rounded-lg py-3.5 px-4 font-mono text-sm mb-5">
                <span className="text-green-500">/sow</span>
                <span className="text-[#a3a3a3]"> K8s migration, 50k users → 500k, 6 weeks</span>
              </div>

              <ul className="space-y-2.5">
                {["AI-generated proposals", "DocuSign integration", "Stripe invoicing", "Slack-native workflow"].map((feature, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-[15px] text-[#e5e5e5]">
                    <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            {/* FormPilot Card */}
            <div className="bg-[#0c0c0c] border border-[#262626] rounded-xl p-7 md:p-8 relative shadow-[0_1px_3px_rgba(0,0,0,0.3)] hover:border-[#333] transition-all duration-200 ease-out">
              <div className="absolute top-5 right-5">
                <span className="px-2.5 py-0.5 text-xs font-medium border border-[#404040] text-[#a3a3a3] rounded-full">
                  Coming Soon
                </span>
              </div>
              <div className="flex items-center gap-3 mb-5">
                <div className="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-[#a3a3a3]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-bold tracking-tight text-[#fafafa]">FormPilot</h3>
                </div>
              </div>

              <p className="text-[#e5e5e5] text-[15px] leading-relaxed mb-5">
                Chrome extension that auto-fills any form with your company data. YC applications, vendor forms, RFPs—done in seconds.
              </p>

              <a
                href="/formpilot"
                className="flex items-center justify-center gap-2.5 w-full min-h-[48px] py-3 px-4 mb-5 rounded-lg bg-[#1a1a1a] border border-[#262626] text-[#fafafa] font-semibold text-[15px] hover:bg-[#222] hover:border-[#404040] focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[#0c0c0c] transition-colors duration-200"
              >
                <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm3.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
                Install for Chrome
              </a>

              <div className="bg-[#141414] border border-[#262626] rounded-lg py-3.5 px-4 text-sm mb-5">
                <div className="flex items-center gap-2 text-[#a3a3a3]">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-500/80" />
                  Detects form fields automatically
                </div>
              </div>

              <ul className="space-y-2.5">
                {["Ambient form detection", "Company data sync", "One-click fill", "Smart field matching"].map((feature, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-[15px] text-[#a3a3a3]">
                    <svg className="w-4 h-4 text-[#525252] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA — single focus */}
      <section className="py-20 md:py-24 px-5 border-t border-[#262626]">
        <div className="max-w-xl mx-auto text-center">
          <div className="w-14 h-14 rounded-xl bg-green-500/10 flex items-center justify-center mx-auto mb-6">
            <svg className="w-7 h-7 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-[#fafafa] mb-3">
            Stop trading time for money
          </h2>
          <p className="text-[#a3a3a3] text-base mb-8 max-w-md mx-auto">
            Join the waitlist for early access. We&apos;re onboarding design partners now.
          </p>
          <a
            href="mailto:dale@prodway.ai"
            className="inline-flex items-center justify-center gap-2 min-h-[48px] px-6 py-3 bg-green-500 text-[#050505] font-semibold text-[15px] rounded-lg hover:bg-[#16a34a] focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[#050505] transition-colors duration-200"
          >
            Get Early Access
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-5 border-t border-[#262626]">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-green-500/12 flex items-center justify-center">
              <svg className="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-sm text-[#a3a3a3]">© 2026 Prodway AI</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-[#a3a3a3]">
            <a href="mailto:dale@prodway.ai" className="hover:text-[#fafafa] focus:outline-none focus:ring-2 focus:ring-[#525252] focus:ring-offset-2 focus:ring-offset-[#050505] rounded transition-colors">Contact</a>
            <a href="#" className="hover:text-[#fafafa] focus:outline-none focus:ring-2 focus:ring-[#525252] focus:ring-offset-2 focus:ring-offset-[#050505] rounded transition-colors">Privacy</a>
            <a href="#" className="hover:text-[#fafafa] focus:outline-none focus:ring-2 focus:ring-[#525252] focus:ring-offset-2 focus:ring-offset-[#050505] rounded transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
