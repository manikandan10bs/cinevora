import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck, Scroll, Cookie, Sparkle } from "@phosphor-icons/react";
import { PageContainer } from "@/components/layout/PageContainer";
import { useDocumentMeta } from "@/hooks/useDocumentMeta";

type StaticPageProps = {
  page: "privacy" | "terms" | "cookies" | "about";
};

const content = {
  privacy: {
    icon: ShieldCheck,
    title: "Privacy Policy",
    updated: "Last updated: April 2025",
    color: "from-blue-500/20 to-background",
    sections: [
      {
        heading: "Information We Collect",
        body: "streamXie is a demonstration platform. We do not collect, store, or process any real personal data. All watch progress, list data, and search history is stored exclusively in your browser&#39;s localStorage and never transmitted to any server.",
      },
      {
        heading: "How We Use Information",
        body: "Since this is a demo application, no data is used for advertising, analytics, or any commercial purposes. The localStorage data exists solely to provide a seamless in-browser experience for demonstration purposes.",
      },
      {
        heading: "Cookies",
        body: "streamXie does not set third-party cookies. Any browser storage used is first-party and limited to application state (your list, watch progress, and recent searches).",
      },
      {
        heading: "Third-Party Services",
        body: "Demo content images are bundled as local project assets for display purposes only. No user data is passed to third-party image services.",
      },
      {
        heading: "Your Rights",
        body: "You can clear all streamXie data at any time by clearing your browser&#39;s localStorage. Navigate to Profile and use the clear history options, or clear your browser storage directly.",
      },
      {
        heading: "Contact",
        body: "This is a demonstration project. For questions about the design or codebase, contact the project team via the associated repository.",
      },
    ],
  },
  terms: {
    icon: Scroll,
    title: "Terms of Use",
    updated: "Last updated: April 2025",
    color: "from-violet-500/20 to-background",
    sections: [
      {
        heading: "Acceptance of Terms",
        body: "By accessing streamXie, you agree that this is a demonstration project built for design and development purposes. No real streaming services, content licenses, or commercial agreements are implied.",
      },
      {
        heading: "Use of the Platform",
        body: "streamXie is provided for educational and portfolio demonstration purposes only. You may explore, share, and reference the platform freely. You may not represent it as a functional commercial streaming service.",
      },
      {
        heading: "Content",
        body: "All titles, descriptions, cast members, and storylines on streamXie are fictional and created for demonstration purposes. Any resemblance to actual productions is coincidental. Placeholder images are bundled as local demo assets.",
      },
      {
        heading: "Intellectual Property",
        body: "The streamXie brand, design system, and codebase are original works. The UI design and component architecture may be referenced for learning but should not be directly copied for commercial use without attribution.",
      },
      {
        heading: "Disclaimer",
        body: "streamXie is provided &#39;as-is&#39; without warranty of any kind. As a demo platform, it may not represent production-level reliability standards.",
      },
      {
        heading: "Changes to Terms",
        body: "These terms may be updated to reflect changes to the demonstration project. Continued use of the platform indicates acceptance of any updated terms.",
      },
    ],
  },
  cookies: {
    icon: Cookie,
    title: "Cookie Settings",
    updated: "Last updated: April 2025",
    color: "from-amber-500/20 to-background",
    sections: [
      {
        heading: "What We Store",
        body: "streamXie uses your browser&#39;s localStorage — not cookies — to save your preferences. No cookies are set by the application itself. Your data stays entirely in your browser.",
      },
      {
        heading: "Essential Storage",
        body: "The following localStorage keys are used: streamxie-my-list (your saved titles), streamxie-watch-progress (per-title playback position), streamxie-search-history (your recent searches), streamxie-avatar (profile avatar), and streamxie-auth-user (demo sign-in state). All are optional and functional only.",
      },
      {
        heading: "Analytics",
        body: "streamXie does not use analytics cookies, tracking pixels, or any behavioral analytics tools. No user data is collected or transmitted.",
      },
      {
        heading: "Advertising",
        body: "streamXie does not serve advertisements and does not use advertising cookies or third-party tracking networks.",
      },
      {
        heading: "Managing Your Storage",
        body: "You can remove all streamXie storage data at any time. Visit your browser settings, navigate to Site Data or Storage, and clear data for this origin. Alternatively, use the clear options in your Profile page.",
      },
      {
        heading: "Third-Party Scripts",
        body: "Google Fonts are loaded for typography. Font requests follow Google&#39;s standard privacy policy. No other third-party scripts are loaded by the application.",
      },
    ],
  },
  about: {
    icon: Sparkle,
    title: "About streamXie",
    updated: "Version 1.0 — 2025",
    color: "from-primary/20 to-background",
    sections: [
      {
        heading: "What is streamXie?",
        body: "streamXie is a premium streaming platform UI concept — a fully designed and coded demonstration of what a modern, cinematic streaming service could look like. Built with React, TypeScript, Tailwind CSS, and Framer Motion.",
      },
      {
        heading: "Design Philosophy",
        body: "Dark by default, seamless by design. streamXie was built with a cinema-first aesthetic: deep dark backgrounds, vivid accent gradients, motion-aware interactions, and a content-forward layout. Every decision prioritizes the content over the chrome.",
      },
      {
        heading: "Content",
        body: "All content on streamXie is entirely fictional — original titles, descriptions, cast, and storylines created specifically for this demonstration. No real media is hosted or distributed.",
      },
      {
        heading: "Technology",
        body: "Built with React 18, TypeScript, Tailwind CSS with a custom design system, Framer Motion for animations, Phosphor Icons, and React Router for navigation. All data is stored in browser localStorage — no backend required.",
      },
      {
        heading: "Features",
        body: "Genre pages, a full video player with progress tracking, My List with toast notifications, a command palette search (⌘K), animated hero banners, detailed movie and series pages, cinematic carousels, and a responsive layout for all screen sizes.",
      },
      {
        heading: "Credits",
        body: "Designed and developed as a portfolio demonstration project. All UI components, design tokens, and layouts are original. Built as a local React and Vite demo.",
      },
    ],
  },
};

export const StaticPage = ({ page }: StaticPageProps) => {
  const info = content[page];
  const Icon = info.icon;

  useDocumentMeta(`${info.title} | streamXie`, info.sections[0]?.body.slice(0, 120) ?? "");

  return (
    <>
      {/* Header */}
      <div className={`relative overflow-hidden bg-gradient-to-b ${info.color} pt-[72px]`}>
        <PageContainer className="relative pb-10 pt-12">
          <Link
            to="/"
            className="mb-6 inline-flex items-center gap-2 rounded-lg border border-border/50 bg-card/40 px-3 py-1.5 text-sm text-muted-foreground backdrop-blur-sm transition-colors hover:border-primary hover:text-primary"
          >
            <ArrowLeft size={15} weight="bold" />
            Back to Home
          </Link>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="flex items-center gap-4"
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-primary text-primary-foreground shadow-lg">
              <Icon size={24} weight="fill" />
            </span>
            <div>
              <h1 className="text-3xl font-bold text-foreground md:text-4xl">{info.title}</h1>
              <p className="mt-1 text-sm text-muted-foreground">{info.updated}</p>
            </div>
          </motion.div>
        </PageContainer>
      </div>

      {/* Sections */}
      <PageContainer className="py-12">
        <div className="mx-auto max-w-3xl space-y-10">
          {info.sections.map((section, i) => (
            <motion.div
              key={section.heading}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: i * 0.07 }}
              className="group"
            >
              <div className="flex items-start gap-4">
                <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-xs font-bold text-primary">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <h2 className="text-base font-semibold text-foreground">{section.heading}</h2>
                  <p
                    className="mt-2 text-sm leading-relaxed text-muted-foreground"
                    dangerouslySetInnerHTML={{ __html: section.body }}
                  />
                </div>
              </div>
              {i < info.sections.length - 1 && (
                <div className="mt-8 border-t border-border/50" />
              )}
            </motion.div>
          ))}
        </div>
      </PageContainer>
    </>
  );
};
