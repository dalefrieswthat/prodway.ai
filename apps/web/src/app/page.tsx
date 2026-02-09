import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Zap, FileText, CreditCard, PenTool, Clock, Sparkles, CheckCircle2 } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen grid-bg">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <Zap className="w-4 h-4 text-primary" />
            </div>
            <span className="font-semibold text-lg">Prodway</span>
          </div>
          <Button variant="outline" size="sm" className="border-primary/30 hover:bg-primary/10">
            Get Early Access
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="animate-slide-up">
            <Badge variant="outline" className="mb-6 border-primary/30 text-primary">
              <Sparkles className="w-3 h-3 mr-1" />
              Now in Private Beta
            </Badge>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 animate-slide-up delay-100">
            Scale your agency
            <br />
            <span className="gradient-text">without hiring</span>
          </h1>
          
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 animate-slide-up delay-200">
            AI tools that handle the boring parts—proposals, contracts, invoicing—so you can focus on the work that matters.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up delay-300">
            <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 gap-2">
              Request Access <ArrowRight className="w-4 h-4" />
            </Button>
            <Button size="lg" variant="outline" className="border-border hover:bg-secondary">
              Watch Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-y border-border/40">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid grid-cols-3 gap-8 text-center">
            <div className="animate-slide-up delay-100">
              <div className="text-4xl font-bold gradient-text">60s</div>
              <div className="text-sm text-muted-foreground mt-1">Request to SOW</div>
            </div>
            <div className="animate-slide-up delay-200">
              <div className="text-4xl font-bold gradient-text">1-Click</div>
              <div className="text-sm text-muted-foreground mt-1">E-Signatures</div>
            </div>
            <div className="animate-slide-up delay-300">
              <div className="text-4xl font-bold gradient-text">0</div>
              <div className="text-sm text-muted-foreground mt-1">Admin Hours</div>
            </div>
          </div>
        </div>
      </section>

      {/* Products Section */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Two products. One mission.</h2>
            <p className="text-muted-foreground text-lg">Eliminate busywork from your consulting business.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* SowFlow Card */}
            <Card className="bg-card/50 border-border/50 glow-green hover:border-primary/30 transition-all duration-300">
              <CardContent className="p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <FileText className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold">SowFlow</h3>
                    <Badge className="bg-primary/20 text-primary border-0 text-xs">Live</Badge>
                  </div>
                </div>
                
                <p className="text-muted-foreground mb-6">
                  Generate professional SOWs from a single Slack command. Send for signature. Invoice automatically.
                </p>

                <div className="bg-secondary/50 rounded-lg p-4 font-mono text-sm mb-6 border border-border/50">
                  <span className="text-primary">/sow</span>
                  <span className="text-muted-foreground"> K8s migration, 50k users → 500k, 6 weeks</span>
                </div>

                <ul className="space-y-3">
                  {["AI-generated proposals", "DocuSign integration", "Stripe invoicing", "Slack-native workflow"].map((feature, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <CheckCircle2 className="w-4 h-4 text-primary" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* FormPilot Card */}
            <Card className="bg-card/50 border-border/50 hover:border-primary/30 transition-all duration-300 relative overflow-hidden">
              <div className="absolute top-4 right-4">
                <Badge variant="outline" className="border-muted-foreground/30 text-muted-foreground text-xs">
                  <Clock className="w-3 h-3 mr-1" />
                  Coming Soon
                </Badge>
              </div>
              <CardContent className="p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
                    <PenTool className="w-6 h-6 text-muted-foreground" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold">FormPilot</h3>
                  </div>
                </div>
                
                <p className="text-muted-foreground mb-6">
                  Chrome extension that auto-fills any form with your company data. YC applications, vendor forms, RFPs—done in seconds.
                </p>

                <div className="bg-secondary/50 rounded-lg p-4 text-sm mb-6 border border-border/50">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    Detects form fields automatically
                  </div>
                </div>

                <ul className="space-y-3">
                  {["Ambient form detection", "Company data sync", "One-click fill", "Smart field matching"].map((feature, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <CheckCircle2 className="w-4 h-4 text-muted-foreground/50" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 border-t border-border/40">
        <div className="max-w-2xl mx-auto text-center">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-8 animate-float">
            <CreditCard className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Stop trading time for money
          </h2>
          <p className="text-muted-foreground text-lg mb-8">
            Join the waitlist for early access. We&apos;re onboarding design partners now.
          </p>
          <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 gap-2">
            Get Early Access <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-border/40">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-primary/20 flex items-center justify-center">
              <Zap className="w-3 h-3 text-primary" />
            </div>
            <span className="text-sm text-muted-foreground">© 2026 Prodway AI</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <a href="mailto:dale@prodway.ai" className="hover:text-foreground transition-colors">Contact</a>
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="hover:text-foreground transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
