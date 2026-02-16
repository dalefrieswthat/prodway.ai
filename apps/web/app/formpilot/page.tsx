import Link from "next/link";

export default function FormPilotInstallPage() {
  return (
    <main className="min-h-screen bg-[#050505] text-[#fafafa] font-sans antialiased">
      <nav className="border-b border-[#262626] bg-[#050505]/90 backdrop-blur-xl">
        <div className="max-w-3xl mx-auto px-5 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2.5 font-semibold text-[17px] text-[#fafafa] hover:text-[#22c55e] transition-colors"
          >
            <div className="w-9 h-9 rounded-lg bg-green-500/12 flex items-center justify-center">
              <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            Prodway
          </Link>
          <Link href="/#products" className="text-sm text-[#a3a3a3] hover:text-[#fafafa] transition-colors">
            Products
          </Link>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-5 py-16">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-14 h-14 rounded-xl bg-white/5 flex items-center justify-center">
            <svg className="w-7 h-7 text-[#a3a3a3]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">FormPilot</h1>
            <p className="text-[#a3a3a3] text-sm mt-0.5">Install the Chrome extension</p>
          </div>
        </div>

        <div className="space-y-8">
          <section>
            <h2 className="text-lg font-semibold mb-4">Install from Chrome Web Store</h2>
            <p className="text-[#a3a3a3] text-[15px] mb-6">
              FormPilot is coming to the Chrome Web Store soon. Until then, you can load it as an unpacked extension from our repo.
            </p>
            <a
              href="https://github.com/dalefrieswthat/prodway.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 min-h-[48px] px-6 py-3 bg-green-500 text-[#050505] font-semibold text-[15px] rounded-lg hover:bg-[#16a34a] focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[#050505] transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm3.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
              </svg>
              Get extension (GitHub)
            </a>
          </section>

          <section className="border-t border-[#262626] pt-8">
            <h2 className="text-lg font-semibold mb-4">Load unpacked (developers)</h2>
            <ol className="list-decimal list-inside space-y-3 text-[15px] text-[#e5e5e5]">
              <li>Clone the repo and open <code className="bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">apps/formpilot</code> in Chrome.</li>
              <li>Go to <code className="bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">chrome://extensions</code>.</li>
              <li>Turn on <strong>Developer mode</strong>, then click <strong>Load unpacked</strong>.</li>
              <li>Select the <code className="bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm">formpilot</code> folder.</li>
              <li>Click the extension icon → <strong>Edit company data</strong> to add your details, then use <strong>Fill form</strong> on any page.</li>
            </ol>
          </section>

          <p className="text-[#a3a3a3] text-sm">
            <Link href="/" className="text-green-500 hover:text-green-400 transition-colors">← Back to Prodway</Link>
          </p>
        </div>
      </div>
    </main>
  );
}
