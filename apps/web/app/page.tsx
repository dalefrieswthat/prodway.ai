export default function Home() {
  return (
    <main className="min-h-screen grid-bg">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-[#262626] bg-[#050505]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
              <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="font-semibold text-lg">Prodway</span>
          </div>
          <a href="mailto:dale@prodway.ai" className="px-4 py-2 text-sm border border-green-500/30 rounded-lg hover:bg-green-500/10 transition-colors">
            Get Early Access
          </a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 text-sm border border-green-500/30 rounded-full text-green-500">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Now in Private Beta
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
            Scale your agency
            <br />
            <span className="gradient-text">without hiring</span>
          </h1>

          <p className="text-xl text-[#a3a3a3] max-w-2xl mx-auto mb-10">
            AI tools that handle the boring parts—proposals, contracts, invoicing—so you can focus on the work that matters.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="mailto:dale@prodway.ai" className="px-6 py-3 bg-green-500 text-black font-medium rounded-lg hover:bg-green-400 transition-colors inline-flex items-center justify-center gap-2">
              Request Access
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </a>
            <button className="px-6 py-3 border border-[#262626] rounded-lg hover:bg-[#1a1a1a] transition-colors">
              Watch Demo
            </button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-y border-[#262626]">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold gradient-text">60s</div>
              <div className="text-sm text-[#a3a3a3] mt-1">Request to SOW</div>
            </div>
            <div>
              <div className="text-4xl font-bold gradient-text">1-Click</div>
              <div className="text-sm text-[#a3a3a3] mt-1">E-Signatures</div>
            </div>
            <div>
              <div className="text-4xl font-bold gradient-text">0</div>
              <div className="text-sm text-[#a3a3a3] mt-1">Admin Hours</div>
            </div>
          </div>
        </div>
      </section>

      {/* Products Section */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Two products. One mission.</h2>
            <p className="text-[#a3a3a3] text-lg">Eliminate busywork from your consulting business.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* SowFlow Card */}
            <div className="bg-[#0a0a0a] border border-[#262626] rounded-2xl p-8 glow-green hover:border-green-500/30 transition-all duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-2xl font-bold">SowFlow</h3>
                  <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-500 rounded-full">Live</span>
                </div>
              </div>

              <p className="text-[#a3a3a3] mb-6">
                Generate professional SOWs from a single Slack command. Send for signature. Invoice automatically.
              </p>

              <div className="bg-[#1a1a1a] rounded-lg p-4 font-mono text-sm mb-6 border border-[#262626]">
                <span className="text-green-500">/sow</span>
                <span className="text-[#a3a3a3]"> K8s migration, 50k users → 500k, 6 weeks</span>
              </div>

              <ul className="space-y-3">
                {["AI-generated proposals", "DocuSign integration", "Stripe invoicing", "Slack-native workflow"].map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-[#a3a3a3]">
                    <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            {/* FormPilot Card */}
            <div className="bg-[#0a0a0a] border border-[#262626] rounded-2xl p-8 relative overflow-hidden hover:border-green-500/30 transition-all duration-300">
              <div className="absolute top-4 right-4">
                <span className="px-2 py-0.5 text-xs border border-[#404040] text-[#a3a3a3] rounded-full inline-flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Coming Soon
                </span>
              </div>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-[#1a1a1a] flex items-center justify-center">
                  <svg className="w-6 h-6 text-[#a3a3a3]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-2xl font-bold">FormPilot</h3>
                </div>
              </div>

              <p className="text-[#a3a3a3] mb-6">
                Chrome extension that auto-fills any form with your company data. YC applications, vendor forms, RFPs—done in seconds.
              </p>

              <div className="bg-[#1a1a1a] rounded-lg p-4 text-sm mb-6 border border-[#262626]">
                <div className="flex items-center gap-2 text-[#a3a3a3]">
                  <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  Detects form fields automatically
                </div>
              </div>

              <ul className="space-y-3">
                {["Ambient form detection", "Company data sync", "One-click fill", "Smart field matching"].map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-[#a3a3a3]">
                    <svg className="w-4 h-4 text-[#404040]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 border-t border-[#262626]">
        <div className="max-w-2xl mx-auto text-center">
          <div className="w-16 h-16 rounded-2xl bg-green-500/10 flex items-center justify-center mx-auto mb-8 animate-float">
            <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Stop trading time for money
          </h2>
          <p className="text-[#a3a3a3] text-lg mb-8">
            Join the waitlist for early access. We&apos;re onboarding design partners now.
          </p>
          <a href="mailto:dale@prodway.ai" className="px-6 py-3 bg-green-500 text-black font-medium rounded-lg hover:bg-green-400 transition-colors inline-flex items-center justify-center gap-2">
            Get Early Access
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-green-500/20 flex items-center justify-center">
              <svg className="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-sm text-[#a3a3a3]">© 2026 Prodway AI</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-[#a3a3a3]">
            <a href="mailto:dale@prodway.ai" className="hover:text-white transition-colors">Contact</a>
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
