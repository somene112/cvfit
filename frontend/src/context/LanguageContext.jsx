'use client';

import { createContext, useContext, useState, useEffect } from 'react';

const dictionary = {
  en: {
    // Landing Page
    'landing.logo': 'CV Fit Analyzer',
    'landing.signIn': 'Sign In',
    'landing.getStarted': 'Get Started',
    'landing.badge': 'Next-Gen AI Analysis',
    'landing.headline.1': 'Land your dream job with',
    'landing.headline.2': 'AI-Powered',
    'landing.headline.3': 'CV matching',
    'landing.subheadline': 'Instantly compare your resume against any job description. Uncover skill gaps, get a precise match score, and receive actionable recommendations to optimize your profile.',
    'landing.ctaPrimary': 'Start Analyzing for Free',
    'landing.features.title': 'Why choose CV Fit Analyzer?',
    'landing.feature1.title': 'Instant Match Scoring',
    'landing.feature1.desc': 'Our advanced AI calculates a precise percentage match between your CV and the target job description in seconds.',
    'landing.feature2.title': 'Skill Gap Detection',
    'landing.feature2.desc': 'Visually identify which exact skills you possess and which critical requirements you are missing from the JD.',
    'landing.feature3.title': 'Actionable Feedback',
    'landing.feature3.desc': 'Get tailored strengths, weaknesses, and step-by-step recommendations to perfectly align your CV before applying.',
    'landing.how.title': 'How it works',
    'landing.how1.title': 'Upload CV',
    'landing.how1.desc': 'Upload your resume in PDF or DOCX format securely.',
    'landing.how2.title': 'Paste Job Details',
    'landing.how2.desc': 'Paste the full job description you are aiming for.',
    'landing.how3.title': 'Get AI Insights',
    'landing.how3.desc': 'Receive your match score, skills analysis, and exportable report.',
    'landing.bottomCta.title': 'Ready to optimize your CV?',
    'landing.bottomCta.desc': 'Join thousands of job seekers landing their dream roles with AI insights.',
    'landing.bottomCta.btn': 'Get Started for Free',
    'landing.footer': '© 2026 CV Fit Analyzer. All rights reserved.',

    // Login Page
    'login.subtitle': 'AI-powered resume analysis platform',
    'login.email': 'Email address',
    'login.password': 'Password',
    'login.btn.signIn': 'Sign in',
    'login.btn.signingIn': 'Signing in...',
    'login.error.empty': 'Please enter both email and password.',
    'login.error.invalid': 'Invalid credentials. Please try again.',
    'login.divider': 'Secure Login',
    'login.footer.text': 'Don\'t have an account?',
    'login.footer.link': 'Create account',
    'register.subtitle': 'Create your account to save CV analysis history',
    'register.fullName': 'Full name',
    'register.btn.create': 'Create account',
    'register.btn.creating': 'Creating account...',
    'register.error.empty': 'Please enter both email and password.',
    'register.error.password': 'Password must be at least 8 characters.',
    'register.error.invalid': 'Could not create account. Please try again.',
    'register.footer.text': 'Already have an account?',
    'register.footer.link': 'Sign in',

    // Dashboard Header
    'header.badge': 'AI',
    'header.logout': 'Logout',

    // Dashboard Page
    'dashboard.title': 'CV Analysis',
    'dashboard.subtitle': 'Upload your CV and paste a job description to get AI-powered matching insights.',

    // Upload CV
    'upload.title': 'Upload CV',
    'upload.subtitle': 'PDF or DOCX, max 10MB',
    'upload.dropzone.title1': 'Drop your CV here, or',
    'upload.dropzone.title2': 'browse files',
    'upload.dropzone.subtext': 'Supports PDF and DOCX formats',
    'upload.progress.uploading': 'Uploading...',
    'upload.error.noFile': 'No file selected',
    'upload.error.format': 'Only PDF and DOCX files are supported.',
    'upload.error.size': 'File size must be under 10MB.',

    // Job Description
    'jd.title': 'Job Description',
    'jd.subtitle': 'Paste the target job description',
    'jd.placeholder': 'Paste the full job description here. Include responsibilities, requirements, qualifications, and preferred skills for the most accurate analysis...',
    'jd.chars': 'characters',

    // Settings
    'settings.title': 'Analysis Settings',
    'settings.subtitle': 'Fine-tune the analysis parameters',
    'settings.role.label': 'Target Role',
    'settings.role.placeholder': 'e.g. Senior Frontend Developer',
    'settings.lang.label': 'Language',
    'settings.strict.label': 'Strictness',

    // Analyze Button
    'analyze.btn.analyzing': 'Analyzing...',
    'analyze.btn.analyze': 'Analyze CV',
    'analyze.alert.noCv': 'Please upload a CV file first.',
    'analyze.alert.noJd': 'Please enter a job description.',

    // Progress
    'progress.title': 'Analysis Progress',
    'progress.step1': 'Upload',
    'progress.step2': 'Analyzing',
    'progress.step3': 'Complete',

    // Results
    'result.header.title': 'Analysis Results',
    'result.header.subtitle': 'AI-powered CV evaluation complete',
    'result.score.label': 'Match Score',
    'result.score.high': 'Excellent Match',
    'result.score.medium': 'Moderate Match',
    'result.score.low': 'Low Match',
    
    // Skills
    'skills.matched': 'Matched Skills',
    'skills.missing': 'Missing Skills',
    'skills.empty.matched': 'No matched skills found',
    'skills.empty.missing': 'No missing skills detected',

    // Feedback
    'feedback.strengths': 'Strengths',
    'feedback.weaknesses': 'Weaknesses',
    'feedback.recommendations': 'Recommendations',
    'feedback.empty.strengths': 'No strengths data available',
    'feedback.empty.weaknesses': 'No weaknesses data available',
    'feedback.empty.recommendations': 'No recommendations available',

    // Download
    'download.btn.downloading': 'Downloading...',
    'download.btn.downloaded': 'Downloaded',
    'download.btn.download': 'Download Report',
    'download.error': 'Failed to download report. Please try again.',
    'result.btn.new': 'New Analysis',

    // Result Dashboard V2
    'resultV2.scoreSummary.title': 'Score Summary',
    'resultV2.scoreSummary.confidence': 'Analysis confidence',
    'resultV2.fitLevel.excellent': 'Excellent Fit',
    'resultV2.fitLevel.good': 'Good Fit',
    'resultV2.fitLevel.partial': 'Partial Fit',
    'resultV2.fitLevel.weak': 'Weak Fit',
    'resultV2.scoreBreakdown.title': 'Score Breakdown',
    'resultV2.scoreBreakdown.subtitle': 'Detailed scoring across evaluation criteria',
    'resultV2.scoreBreakdown.weight': 'Weight',
    'resultV2.matchedSkills.title': 'Matched Skills',
    'resultV2.matchedSkills.found': 'skills matched',
    'resultV2.matchedSkills.confidence': 'Confidence',
    'resultV2.matchedSkills.evidenceCount': 'evidence items',
    'resultV2.evidence.title': 'Evidence',
    'resultV2.evidence.found': 'evidence items',
    'resultV2.evidence.snippet': 'Evidence snippet',
    'resultV2.evidence.source.cv': 'CV',
    'resultV2.evidence.source.jd': 'JD',
    'resultV2.evidence.section': 'Section',
    'resultV2.missingSkills.title': 'Missing Skills',
    'resultV2.missingSkills.found': 'skills without evidence',
    'resultV2.missingSkills.noEvidence': 'No evidence found',
    'resultV2.missingSkills.reason': 'Reason',
    'resultV2.missingSkills.suggestion': 'Suggestion',
    'resultV2.improvement.title': 'Improvement Actions',
    'resultV2.improvement.subtitle': 'Actionable steps to strengthen your profile',
    'resultV2.improvement.priority.high': 'High',
    'resultV2.improvement.priority.medium': 'Medium',
    'resultV2.improvement.priority.low': 'Low',
    'resultV2.improvement.safeNote': 'Safe rewrite note',
    'resultV2.limitations.title': 'Limitations & Disclaimers',
    'resultV2.limitations.disclaimer': 'Please review the following caveats',
    'resultV2.empty.title': 'No Results Available',
    'resultV2.empty.description': 'The analysis did not return any meaningful data. Please try again with a different CV or job description.',
    'resultV2.empty.retry': 'Try Again',
    'resultV2.error.title': 'Something Went Wrong',
    'resultV2.error.description': 'An error occurred while loading the analysis results. Please try again.',
    'resultV2.error.retry': 'Retry',

    // Phase 4 — Improvement Action Plan
    'phase4.improvement.title': 'Improvement Action Plan',
    'phase4.improvement.subtitle': 'Prioritized steps to strengthen your CV',
    'phase4.improvement.action': 'Action',
    'phase4.improvement.reason': 'Reason',
    'phase4.improvement.linkedSkill': 'Linked Skill',
    'phase4.improvement.safeSuggestion': 'Suggestion',
    'phase4.improvement.status.pending': 'Pending',
    'phase4.improvement.status.done': 'Done',
    'phase4.improvement.expandDetails': 'Show details',
    'phase4.improvement.collapseDetails': 'Hide details',
    'phase4.improvement.type.skill_gap': 'Skill Gap',
    'phase4.improvement.type.cv_rewrite': 'CV Rewrite',
    'phase4.improvement.empty': 'No improvement actions available.',

    // Phase 4 — Safe Rewrite Suggestions
    'phase4.safeRewrite.title': 'Safe Rewrite Suggestions',
    'phase4.safeRewrite.subtitle': 'Suggested improvements for your CV bullets',
    'phase4.safeRewrite.warning': '⚠️ Only include skills and experience that are actually true.',
    'phase4.safeRewrite.warningDetail': 'Do not invent skills, projects, metrics, or responsibilities. These suggestions are starting points — only use them if they reflect your real experience.',
    'phase4.safeRewrite.currentEvidence': 'Current Evidence',
    'phase4.safeRewrite.suggestedRewrite': 'Suggested Rewrite',
    'phase4.safeRewrite.guardrail': 'Safety Note',
    'phase4.safeRewrite.empty': 'No rewrite suggestions available.',

    // Phase 4 — Interview Prep Pack
    'phase4.interviewPrep.title': 'Interview Prep Pack',
    'phase4.interviewPrep.subtitle': 'Likely interview questions based on your CV and the JD',
    'phase4.interviewPrep.whyThisQuestion': 'Why this question?',
    'phase4.interviewPrep.suggestedOutline': 'Suggested Answer Outline',
    'phase4.interviewPrep.relatedJd': 'Related JD Requirement',
    'phase4.interviewPrep.relatedCv': 'Related CV Evidence',
    'phase4.interviewPrep.risk': 'Risk if you can\'t answer',
    'phase4.interviewPrep.type.behavioral': 'Behavioral',
    'phase4.interviewPrep.type.technical': 'Technical',
    'phase4.interviewPrep.type.situational': 'Situational',
    'phase4.interviewPrep.type.general': 'General',
    'phase4.interviewPrep.empty': 'No interview prep questions available yet.',
    'phase4.interviewPrep.questions': 'questions',

    // Phase 4 — Learning Roadmap
    'phase4.roadmap.title': 'Learning Roadmap',
    'phase4.roadmap.subtitle': 'Skills to learn and how to showcase them on your CV',
    'phase4.roadmap.why': 'Why learn this?',
    'phase4.roadmap.topics': 'Topics to Cover',
    'phase4.roadmap.miniProject': 'Mini Project Idea',
    'phase4.roadmap.cvEvidence': 'What to Add to CV After Learning',
    'phase4.roadmap.empty': 'No learning roadmap available yet.',

    // Phase 4 — Re-analysis Upload
    'phase4.reanalysis.title': 'Re-analyze with Updated CV',
    'phase4.reanalysis.subtitle': 'Upload your revised CV to see how your score improves',
    'phase4.reanalysis.dropzone': 'Drop your revised CV here, or browse',
    'phase4.reanalysis.uploading': 'Uploading revised CV...',
    'phase4.reanalysis.analyzing': 'Re-analyzing your CV...',
    'phase4.reanalysis.success': 'Re-analysis complete!',
    'phase4.reanalysis.error': 'Re-analysis failed. Please try again.',
    'phase4.reanalysis.compareBtn': 'View Comparison',

    // Phase 4 — Comparison Dashboard
    'phase4.comparison.title': 'Comparison Dashboard',
    'phase4.comparison.subtitle': 'See how your revised CV compares',
    'phase4.comparison.previous': 'Previous',
    'phase4.comparison.current': 'Current',
    'phase4.comparison.delta': 'Change',
    'phase4.comparison.resolvedGaps': 'Resolved Gaps',
    'phase4.comparison.stillMissing': 'Still Missing',
    'phase4.comparison.newlyMatched': 'Newly Matched Skills',
    'phase4.comparison.stuffingWarning': 'Keyword Stuffing Warning',
    'phase4.comparison.stuffingDetail': 'Score increased significantly but evidence count did not grow proportionally. Ensure all claims are genuine.',
    'phase4.comparison.nextActions': 'Remaining Actions',
    'phase4.comparison.unavailable': 'Comparison is not available. Run a re-analysis first.',
    'phase4.comparison.noChange': 'No change',
    'phase4.comparison.improved': 'Improved',
    'phase4.comparison.regressed': 'Regressed',

    // Phase 4 — Evidence Section
    'phase4.evidence.title': 'Evidence',
    'phase4.evidence.subtitle': 'Supporting evidence from your CV and the JD',
    'phase4.evidence.showAll': 'Show all evidence',
    'phase4.evidence.hideAll': 'Collapse evidence',
    'phase4.evidence.showMore': 'more',
    'phase4.evidence.showFull': 'Show full text',
    'phase4.evidence.showLess': 'Show less',
    'phase4.evidence.empty': 'No evidence data available.',

    // Phase 4 — History
    'phase4.history.viewResult': 'View Result',
    'phase4.history.compare': 'Compare',
    'phase4.history.revision': 'Revision',
    'phase4.history.noAccessToken': 'Result no longer accessible'
  },
  vi: {
    // Landing Page
    'landing.logo': 'CV Fit Analyzer',
    'landing.signIn': 'Đăng nhập',
    'landing.getStarted': 'Bắt đầu ngay',
    'landing.badge': 'Phân tích bằng AI',
    'landing.headline.1': 'Chinh phục công việc mơ ước với phân tích CV',
    'landing.headline.2': 'Bằng AI',
    'landing.headline.3': '',
    'landing.subheadline': 'So sánh ngay lập tức sơ yếu lý lịch của bạn với bất kỳ mô tả công việc nào. Khám phá lỗ hổng kỹ năng, nhận điểm số độ phù hợp và các đề xuất tối ưu hồ sơ.',
    'landing.ctaPrimary': 'Bắt đầu phân tích miễn phí',
    'landing.features.title': 'Tại sao chọn CV Fit Analyzer?',
    'landing.feature1.title': 'Chấm điểm mức độ phù hợp',
    'landing.feature1.desc': 'AI tính toán chính xác phần trăm phù hợp giữa CV của bạn và yêu cầu công việc chỉ trong vài giây.',
    'landing.feature2.title': 'Nhận diện kỹ năng thiếu sót',
    'landing.feature2.desc': 'Xác định trực quan những kỹ năng bạn đang có và những yêu cầu quan trọng mà bạn còn thiếu.',
    'landing.feature3.title': 'Đề xuất hành động',
    'landing.feature3.desc': 'Nhận phản hồi chi tiết về điểm mạnh, điểm yếu và các bước tối ưu CV trước khi ứng tuyển.',
    'landing.how.title': 'Cách hoạt động',
    'landing.how1.title': 'Tải lên CV',
    'landing.how1.desc': 'Tải lên sơ yếu lý lịch của bạn (định dạng PDF hoặc DOCX).',
    'landing.how2.title': 'Nhập mô tả công việc',
    'landing.how2.desc': 'Dán toàn bộ yêu cầu của vị trí bạn muốn ứng tuyển.',
    'landing.how3.title': 'Nhận phân tích từ AI',
    'landing.how3.desc': 'Nhận điểm phù hợp, phân tích kỹ năng và xuất báo cáo.',
    'landing.bottomCta.title': 'Sẵn sàng tối ưu hóa CV của bạn?',
    'landing.bottomCta.desc': 'Tham gia cùng hàng ngàn ứng viên đang chinh phục công việc mơ ước với công nghệ AI.',
    'landing.bottomCta.btn': 'Bắt đầu ngay hoàn toàn miễn phí',
    'landing.footer': '© 2026 CV Fit Analyzer. Đã đăng ký bản quyền.',

    // Login Page
    'login.subtitle': 'Nền tảng phân tích hồ sơ bằng AI',
    'login.email': 'Địa chỉ Email',
    'login.password': 'Mật khẩu',
    'login.btn.signIn': 'Đăng nhập',
    'login.btn.signingIn': 'Đang đăng nhập...',
    'login.error.empty': 'Vui lòng nhập cả email và mật khẩu.',
    'login.error.invalid': 'Thông tin đăng nhập không hợp lệ. Thử lại.',
    'login.divider': 'Đăng nhập bảo mật',
    'login.footer.text': 'Chưa có tài khoản?',
    'login.footer.link': 'Tạo tài khoản',
    'register.subtitle': 'Tạo tài khoản để lưu lịch sử phân tích CV',
    'register.fullName': 'Họ và tên',
    'register.btn.create': 'Tạo tài khoản',
    'register.btn.creating': 'Đang tạo tài khoản...',
    'register.error.empty': 'Vui lòng nhập cả email và mật khẩu.',
    'register.error.password': 'Mật khẩu phải có ít nhất 8 ký tự.',
    'register.error.invalid': 'Không thể tạo tài khoản. Vui lòng thử lại.',
    'register.footer.text': 'Đã có tài khoản?',
    'register.footer.link': 'Đăng nhập',

    // Dashboard Header
    'header.badge': 'AI',
    'header.logout': 'Đăng xuất',

    // Dashboard Page
    'dashboard.title': 'Phân tích CV',
    'dashboard.subtitle': 'Tải CV lên và dán mô tả công việc để AI tự động so khớp.',

    // Upload CV
    'upload.title': 'Tải CV lên',
    'upload.subtitle': 'PDF hoặc DOCX, tối đa 10MB',
    'upload.dropzone.title1': 'Kéo thả CV vào đây, hoặc',
    'upload.dropzone.title2': 'duyệt file',
    'upload.dropzone.subtext': 'Hỗ trợ định dạng PDF và DOCX',
    'upload.progress.uploading': 'Đang tải lên...',
    'upload.error.noFile': 'Chưa chọn file',
    'upload.error.format': 'Chỉ hỗ trợ file PDF và DOCX.',
    'upload.error.size': 'Kích thước file phải dưới 10MB.',

    // Job Description
    'jd.title': 'Mô tả công việc (JD)',
    'jd.subtitle': 'Dán nội dung mô tả công việc',
    'jd.placeholder': 'Dán toàn bộ mô tả công việc vào đây. Bao gồm trách nhiệm, yêu cầu, bằng cấp và kỹ năng ưu tiên để phân tích chính xác nhất...',
    'jd.chars': 'ký tự',

    // Settings
    'settings.title': 'Cấu hình phân tích',
    'settings.subtitle': 'Tinh chỉnh các thông số phân tích',
    'settings.role.label': 'Vị trí mục tiêu',
    'settings.role.placeholder': 'VD: Senior Frontend Developer',
    'settings.lang.label': 'Ngôn ngữ',
    'settings.strict.label': 'Độ khắt khe',

    // Analyze Button
    'analyze.btn.analyzing': 'Đang phân tích...',
    'analyze.btn.analyze': 'Phân tích CV ngay',
    'analyze.alert.noCv': 'Vui lòng tải lên file CV trước.',
    'analyze.alert.noJd': 'Vui lòng nhập mô tả công việc.',

    // Progress
    'progress.title': 'Tiến trình phân tích',
    'progress.step1': 'Tải lên',
    'progress.step2': 'Đang phân tích',
    'progress.step3': 'Hoàn thành',

    // Results
    'result.header.title': 'Kết quả phân tích',
    'result.header.subtitle': 'Hệ thống AI đã hoàn tất quá trình đánh giá',
    'result.score.label': 'Độ Phù Hợp',
    'result.score.high': 'Phù Hợp Xuất Sắc',
    'result.score.medium': 'Phù Hợp Trung Bình',
    'result.score.low': 'Mức Độ Phù Hợp Thấp',
    
    // Skills
    'skills.matched': 'Kỹ năng đáp ứng',
    'skills.missing': 'Kỹ năng còn thiếu',
    'skills.empty.matched': 'Không tìm thấy kỹ năng đáp ứng',
    'skills.empty.missing': 'Không phát hiện kỹ năng nào còn thiếu',

    // Feedback
    'feedback.strengths': 'Điểm mạnh',
    'feedback.weaknesses': 'Điểm yếu',
    'feedback.recommendations': 'Khuyến nghị cải thiện',
    'feedback.empty.strengths': 'Chưa có dữ liệu về điểm mạnh',
    'feedback.empty.weaknesses': 'Chưa có dữ liệu về điểm yếu',
    'feedback.empty.recommendations': 'Chưa có đề xuất nào',

    // Download
    'download.btn.downloading': 'Đang tải xuống...',
    'download.btn.downloaded': 'Đã tải',
    'download.btn.download': 'Tải báo cáo chi tiết',
    'download.error': 'Lỗi khi tải báo cáo. Vui lòng thử lại.',
    'result.btn.new': 'Phân tích mới',

    // Result Dashboard V2
    'resultV2.scoreSummary.title': 'Tổng quan điểm',
    'resultV2.scoreSummary.confidence': 'Độ tin cậy phân tích',
    'resultV2.fitLevel.excellent': 'Phù hợp xuất sắc',
    'resultV2.fitLevel.good': 'Phù hợp tốt',
    'resultV2.fitLevel.partial': 'Phù hợp một phần',
    'resultV2.fitLevel.weak': 'Phù hợp yếu',
    'resultV2.scoreBreakdown.title': 'Chi tiết điểm',
    'resultV2.scoreBreakdown.subtitle': 'Đánh giá chi tiết theo từng tiêu chí',
    'resultV2.scoreBreakdown.weight': 'Trọng số',
    'resultV2.matchedSkills.title': 'Kỹ năng đáp ứng',
    'resultV2.matchedSkills.found': 'kỹ năng phù hợp',
    'resultV2.matchedSkills.confidence': 'Độ tin cậy',
    'resultV2.matchedSkills.evidenceCount': 'bằng chứng',
    'resultV2.evidence.title': 'Bằng chứng',
    'resultV2.evidence.found': 'mục bằng chứng',
    'resultV2.evidence.snippet': 'Trích đoạn',
    'resultV2.evidence.source.cv': 'CV',
    'resultV2.evidence.source.jd': 'JD',
    'resultV2.evidence.section': 'Phần',
    'resultV2.missingSkills.title': 'Kỹ năng chưa tìm thấy',
    'resultV2.missingSkills.found': 'kỹ năng chưa có bằng chứng',
    'resultV2.missingSkills.noEvidence': 'Không tìm thấy bằng chứng',
    'resultV2.missingSkills.reason': 'Lý do',
    'resultV2.missingSkills.suggestion': 'Gợi ý',
    'resultV2.improvement.title': 'Hành động cải thiện',
    'resultV2.improvement.subtitle': 'Các bước cụ thể để tăng cường hồ sơ',
    'resultV2.improvement.priority.high': 'Cao',
    'resultV2.improvement.priority.medium': 'Trung bình',
    'resultV2.improvement.priority.low': 'Thấp',
    'resultV2.improvement.safeNote': 'Lưu ý viết lại an toàn',
    'resultV2.limitations.title': 'Giới hạn & Tuyên bố miễn trừ',
    'resultV2.limitations.disclaimer': 'Vui lòng xem xét các lưu ý sau',
    'resultV2.empty.title': 'Không có kết quả',
    'resultV2.empty.description': 'Phân tích không trả về dữ liệu hữu ích. Vui lòng thử lại với CV hoặc mô tả công việc khác.',
    'resultV2.empty.retry': 'Thử lại',
    'resultV2.error.title': 'Đã xảy ra lỗi',
    'resultV2.error.description': 'Có lỗi khi tải kết quả phân tích. Vui lòng thử lại.',
    'resultV2.error.retry': 'Thử lại',

    // Phase 4 — Improvement Action Plan
    'phase4.improvement.title': 'Kế hoạch cải thiện',
    'phase4.improvement.subtitle': 'Các bước ưu tiên để tăng cường CV',
    'phase4.improvement.action': 'Hành động',
    'phase4.improvement.reason': 'Lý do',
    'phase4.improvement.linkedSkill': 'Kỹ năng liên quan',
    'phase4.improvement.safeSuggestion': 'Gợi ý',
    'phase4.improvement.status.pending': 'Chờ xử lý',
    'phase4.improvement.status.done': 'Hoàn thành',
    'phase4.improvement.expandDetails': 'Xem chi tiết',
    'phase4.improvement.collapseDetails': 'Ẩn chi tiết',
    'phase4.improvement.type.skill_gap': 'Thiếu kỹ năng',
    'phase4.improvement.type.cv_rewrite': 'Viết lại CV',
    'phase4.improvement.empty': 'Không có hành động cải thiện.',

    // Phase 4 — Safe Rewrite
    'phase4.safeRewrite.title': 'Gợi ý viết lại an toàn',
    'phase4.safeRewrite.subtitle': 'Cải thiện nội dung CV của bạn',
    'phase4.safeRewrite.warning': '⚠️ Chỉ thêm kỹ năng và kinh nghiệm thực tế của bạn.',
    'phase4.safeRewrite.warningDetail': 'Không bịa đặt kỹ năng, dự án, số liệu hay trách nhiệm. Các gợi ý chỉ là điểm khởi đầu — chỉ sử dụng nếu phản ánh kinh nghiệm thực.',
    'phase4.safeRewrite.currentEvidence': 'Bằng chứng hiện tại',
    'phase4.safeRewrite.suggestedRewrite': 'Gợi ý viết lại',
    'phase4.safeRewrite.guardrail': 'Lưu ý an toàn',
    'phase4.safeRewrite.empty': 'Không có gợi ý viết lại.',

    // Phase 4 — Interview Prep
    'phase4.interviewPrep.title': 'Chuẩn bị phỏng vấn',
    'phase4.interviewPrep.subtitle': 'Câu hỏi phỏng vấn dự kiến dựa trên CV và JD',
    'phase4.interviewPrep.whyThisQuestion': 'Tại sao hỏi câu này?',
    'phase4.interviewPrep.suggestedOutline': 'Gợi ý trả lời',
    'phase4.interviewPrep.relatedJd': 'Yêu cầu JD liên quan',
    'phase4.interviewPrep.relatedCv': 'Bằng chứng CV liên quan',
    'phase4.interviewPrep.risk': 'Rủi ro nếu không trả lời được',
    'phase4.interviewPrep.type.behavioral': 'Hành vi',
    'phase4.interviewPrep.type.technical': 'Kỹ thuật',
    'phase4.interviewPrep.type.situational': 'Tình huống',
    'phase4.interviewPrep.type.general': 'Chung',
    'phase4.interviewPrep.empty': 'Chưa có câu hỏi phỏng vấn.',
    'phase4.interviewPrep.questions': 'câu hỏi',

    // Phase 4 — Learning Roadmap
    'phase4.roadmap.title': 'Lộ trình học tập',
    'phase4.roadmap.subtitle': 'Kỹ năng cần học và cách thể hiện trên CV',
    'phase4.roadmap.why': 'Tại sao cần học?',
    'phase4.roadmap.topics': 'Chủ đề cần nắm',
    'phase4.roadmap.miniProject': 'Ý tưởng dự án nhỏ',
    'phase4.roadmap.cvEvidence': 'Thêm vào CV sau khi học',
    'phase4.roadmap.empty': 'Chưa có lộ trình học tập.',

    // Phase 4 — Re-analysis
    'phase4.reanalysis.title': 'Phân tích lại với CV mới',
    'phase4.reanalysis.subtitle': 'Tải lên CV đã chỉnh sửa để xem điểm cải thiện',
    'phase4.reanalysis.dropzone': 'Kéo thả CV mới vào đây, hoặc duyệt',
    'phase4.reanalysis.uploading': 'Đang tải lên CV mới...',
    'phase4.reanalysis.analyzing': 'Đang phân tích lại CV...',
    'phase4.reanalysis.success': 'Phân tích lại hoàn tất!',
    'phase4.reanalysis.error': 'Phân tích lại thất bại. Vui lòng thử lại.',
    'phase4.reanalysis.compareBtn': 'Xem so sánh',

    // Phase 4 — Comparison
    'phase4.comparison.title': 'Bảng so sánh',
    'phase4.comparison.subtitle': 'So sánh CV trước và sau chỉnh sửa',
    'phase4.comparison.previous': 'Trước',
    'phase4.comparison.current': 'Hiện tại',
    'phase4.comparison.delta': 'Thay đổi',
    'phase4.comparison.resolvedGaps': 'Lỗ hổng đã khắc phục',
    'phase4.comparison.stillMissing': 'Vẫn còn thiếu',
    'phase4.comparison.newlyMatched': 'Kỹ năng mới đáp ứng',
    'phase4.comparison.stuffingWarning': 'Cảnh báo nhồi từ khóa',
    'phase4.comparison.stuffingDetail': 'Điểm tăng đáng kể nhưng số lượng bằng chứng không tăng tương ứng.',
    'phase4.comparison.nextActions': 'Hành động còn lại',
    'phase4.comparison.unavailable': 'Chưa có dữ liệu so sánh. Hãy phân tích lại trước.',
    'phase4.comparison.noChange': 'Không đổi',
    'phase4.comparison.improved': 'Cải thiện',
    'phase4.comparison.regressed': 'Giảm',

    // Phase 4 — Evidence
    'phase4.evidence.title': 'Bằng chứng',
    'phase4.evidence.subtitle': 'Bằng chứng từ CV và JD',
    'phase4.evidence.showAll': 'Xem tất cả bằng chứng',
    'phase4.evidence.hideAll': 'Thu gọn bằng chứng',
    'phase4.evidence.showMore': 'thêm',
    'phase4.evidence.showFull': 'Xem toàn bộ',
    'phase4.evidence.showLess': 'Thu gọn',
    'phase4.evidence.empty': 'Không có dữ liệu bằng chứng.',

    // Phase 4 — History
    'phase4.history.viewResult': 'Xem kết quả',
    'phase4.history.compare': 'So sánh',
    'phase4.history.revision': 'Phiên bản',
    'phase4.history.noAccessToken': 'Kết quả không còn truy cập được'
  }
};

export const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState('vi'); // Default language is Vietnamese

  useEffect(() => {
    const savedLang = localStorage.getItem('app_lang');
    if (savedLang === 'en' || savedLang === 'vi') {
      setLang(savedLang);
    }
  }, []);

  const changeLanguage = (newLang) => {
    setLang(newLang);
    localStorage.setItem('app_lang', newLang);
  };

  const t = (key) => {
    return dictionary[lang]?.[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, changeLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
