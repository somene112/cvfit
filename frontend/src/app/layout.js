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
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#2563EB" />
      </head>
      <body>
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
