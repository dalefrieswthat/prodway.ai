'use client';

import { useState, FormEvent } from 'react';

const API_URL = 'https://api.prodway.ai/api/contact';

export default function ContactForm() {
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus('sending');
    setErrorMsg('');

    const form = e.currentTarget;
    const data = {
      name: (form.elements.namedItem('name') as HTMLInputElement).value.trim(),
      email: (form.elements.namedItem('email') as HTMLInputElement).value.trim(),
      company: (form.elements.namedItem('company') as HTMLInputElement).value.trim(),
      interest: (form.elements.namedItem('interest') as HTMLSelectElement).value,
      message: (form.elements.namedItem('message') as HTMLTextAreaElement).value.trim(),
    };

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to send');
      setStatus('sent');
    } catch {
      setErrorMsg('Something went wrong. Please try again or email dale@prodway.ai directly.');
      setStatus('error');
    }
  }

  return (
    <section id="contact" className="py-20 md:py-24 px-5 border-t border-[#262626]">
      <div className="max-w-[640px] mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-[#fafafa] mb-3">
            Let&apos;s talk about your project
          </h2>
          <p className="text-[#a3a3a3] text-base max-w-md mx-auto">
            Tell us what you&apos;re building. We&apos;ll get back to you within 24 hours.
          </p>
        </div>

        <div className="bg-[#0c0c0c] border border-[#262626] rounded-xl p-7 md:p-8">
          {status === 'sent' ? (
            <div className="text-center py-8">
              <svg className="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-xl font-bold text-[#fafafa] mb-2">Message sent!</h3>
              <p className="text-[#a3a3a3] text-[15px]">
                Thanks for reaching out. We&apos;ll get back to you within 24 hours.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="grid sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label htmlFor="name" className="block text-[13px] font-medium text-[#a3a3a3] mb-1.5">
                    Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    required
                    placeholder="Jane Smith"
                    className="w-full px-4 py-3 bg-white/[0.03] border border-[#262626] rounded-lg text-[#fafafa] text-[15px] placeholder:text-[#525252] focus:outline-none focus:border-green-500 transition-colors"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-[13px] font-medium text-[#a3a3a3] mb-1.5">
                    Email *
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    required
                    placeholder="jane@company.com"
                    className="w-full px-4 py-3 bg-white/[0.03] border border-[#262626] rounded-lg text-[#fafafa] text-[15px] placeholder:text-[#525252] focus:outline-none focus:border-green-500 transition-colors"
                  />
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label htmlFor="company" className="block text-[13px] font-medium text-[#a3a3a3] mb-1.5">
                    Company
                  </label>
                  <input
                    type="text"
                    id="company"
                    name="company"
                    placeholder="Acme Inc."
                    className="w-full px-4 py-3 bg-white/[0.03] border border-[#262626] rounded-lg text-[#fafafa] text-[15px] placeholder:text-[#525252] focus:outline-none focus:border-green-500 transition-colors"
                  />
                </div>
                <div>
                  <label htmlFor="interest" className="block text-[13px] font-medium text-[#a3a3a3] mb-1.5">
                    Interested in
                  </label>
                  <select
                    id="interest"
                    name="interest"
                    className="w-full px-4 py-3 bg-white/[0.03] border border-[#262626] rounded-lg text-[#fafafa] text-[15px] focus:outline-none focus:border-green-500 transition-colors appearance-none"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23a3a3a3' viewBox='0 0 24 24'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 1rem center',
                    }}
                  >
                    <option value="">Select one...</option>
                    <option value="sowflow">SowFlow (SOW generation)</option>
                    <option value="formpilot">FormPilot (form auto-fill)</option>
                    <option value="consulting">Consulting services</option>
                    <option value="both">Both products</option>
                    <option value="other">Something else</option>
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label htmlFor="message" className="block text-[13px] font-medium text-[#a3a3a3] mb-1.5">
                  What are you building? *
                </label>
                <textarea
                  id="message"
                  name="message"
                  required
                  rows={4}
                  placeholder="Tell us about your project, team size, and what you need help with..."
                  className="w-full px-4 py-3 bg-white/[0.03] border border-[#262626] rounded-lg text-[#fafafa] text-[15px] placeholder:text-[#525252] focus:outline-none focus:border-green-500 transition-colors resize-y min-h-[100px]"
                />
              </div>

              <button
                type="submit"
                disabled={status === 'sending'}
                className="inline-flex items-center justify-center gap-2 w-full min-h-[48px] px-6 py-3 bg-green-500 text-[#050505] font-semibold text-[15px] rounded-lg hover:bg-[#16a34a] focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[#050505] transition-colors duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {status === 'sending' ? 'Sending...' : (
                  <>
                    Send Message
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  </>
                )}
              </button>

              {status === 'error' && (
                <div className="mt-3 px-4 py-3 bg-red-500/10 border border-red-500/25 rounded-lg text-red-400 text-sm">
                  {errorMsg}
                </div>
              )}
            </form>
          )}
        </div>
      </div>
    </section>
  );
}
