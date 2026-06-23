import { GoogleTagManager } from '@next/third-parties/google';
import { LanguageProvider } from '@/context/LanguageContext';
import './globals.css';

export const metadata = {
  title: 'AI CV Fit Analyzer — Smart Resume Analysis',
  description:
    'Analyze your CV against job descriptions with AI-powered matching. Get instant scores, skill gap analysis, and actionable recommendations.',
  keywords: 'CV analysis, resume, AI, job matching, skill gap, career',
  openGraph: {
    title: 'AI CV Fit Analyzer',
    description: 'AI-powered CV analysis and job matching platform',
    type: 'website',
  },
};

export default function RootLayout({ children }) {
  const gtmId = process.env.NEXT_PUBLIC_GTM_ID;

  return (
    <html lang="en">
      {gtmId ? <GoogleTagManager gtmId={gtmId} /> : null}
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap"
          rel="stylesheet"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0EA5E9" />
      </head>
      <body>
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
