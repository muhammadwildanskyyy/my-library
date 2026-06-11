import Link from "next/link";
import { ArrowRight, BookOpen, Bot, Library, Sparkles } from "lucide-react";

export default function RootPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-aged-paper to-parchment selection:bg-brass/30 text-ink">
      {/* Header / Nav */}
      <header className="px-6 py-6 max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Library className="w-6 h-6 text-mahogany" />
          <span className="font-bold text-xl tracking-tight text-ink">
            Aethelgard
          </span>
        </div>
        <nav>
          <Link
            href="/library"
            className="text-sm font-medium hover:text-mahogany transition-colors"
          >
            Go to Library
          </Link>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-6 pt-20 pb-24 sm:pt-32 sm:pb-32">
        <div className="flex flex-col items-center text-center space-y-8 max-w-3xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brass/20 text-mahogany text-xs font-semibold tracking-wide border border-brass/30">
            <Sparkles className="w-3.5 h-3.5" />
            Your AI-Powered Study Companion
          </div>

          <h1 className="text-5xl sm:text-7xl font-bold tracking-tight text-ink leading-[1.1]">
            Build Your Own <br className="hidden sm:block" />
            <span className="text-mahogany relative">
              Intelligent Library
              {/* Decorative underline */}
              <svg className="absolute w-full h-3 -bottom-1 left-0 text-brass opacity-60" viewBox="0 0 100 10" preserveAspectRatio="none">
                <path d="M0 5 Q 50 10 100 5" stroke="currentColor" strokeWidth="2" fill="none" />
              </svg>
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-ink/70 max-w-2xl leading-relaxed">
            Upload your PDFs, organize them on beautiful shelves, and chat with an AI assistant that instantly reads, comprehends, and finds answers directly from your books.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 pt-4">
            <Link
              href="/library"
              className="group flex items-center gap-2 bg-mahogany hover:bg-mahogany-light text-white px-8 py-3.5 rounded-md font-medium transition-all shadow-lg shadow-mahogany/20 hover:shadow-mahogany/40"
            >
              Enter the Library
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="#features"
              className="text-sm font-medium text-ink hover:text-mahogany transition-colors px-6 py-3"
            >
              Learn more
            </a>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="mt-32 sm:mt-40 grid grid-cols-1 md:grid-cols-3 gap-8 sm:gap-12">
          {/* Feature 1 */}
          <div className="flex flex-col items-start space-y-4 p-6 rounded-2xl bg-white/40 backdrop-blur-sm border border-border/40 hover:bg-white/60 transition-colors shadow-sm">
            <div className="p-3 bg-mahogany/10 text-mahogany rounded-xl">
              <Library className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-ink">Organize with Shelves</h3>
            <p className="text-ink/70 leading-relaxed text-sm">
              Keep your digital documents tidy. Create beautiful shelves to categorize your PDFs and access them effortlessly through an elegant interface.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="flex flex-col items-start space-y-4 p-6 rounded-2xl bg-white/40 backdrop-blur-sm border border-border/40 hover:bg-white/60 transition-colors shadow-sm">
            <div className="p-3 bg-brass/20 text-amber-700 rounded-xl">
              <BookOpen className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-ink">Read in Any Mode</h3>
            <p className="text-ink/70 leading-relaxed text-sm">
              View your books directly in the browser as a rich PDF, or switch to the distraction-free Text Reader mode for a continuous reading experience.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="flex flex-col items-start space-y-4 p-6 rounded-2xl bg-white/40 backdrop-blur-sm border border-border/40 hover:bg-white/60 transition-colors shadow-sm">
            <div className="p-3 bg-emerald-500/10 text-emerald-700 rounded-xl">
              <Bot className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-ink">Ask the Librarian</h3>
            <p className="text-ink/70 leading-relaxed text-sm">
              Have a question? Just ask. Our AI instantly searches through your entire library or specific shelves and gives you answers with exact page citations.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 bg-background/50 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-sm text-ink/50">
          <p>© {new Date().getFullYear()} Intelligent Library. Built with Next.js & FastAPI.</p>
        </div>
      </footer>
    </div>
  );
}
