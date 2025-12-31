import { useState, useEffect } from 'react';
import type { Job } from '../types/job';
import type { GeneratedCoverLetter, CoverLetterStyle } from '../types/coverLetter';

interface CoverLetterEditorProps {
  job: Job;
  selectedCVBlocks?: number[];
  onSaved?: (letter: GeneratedCoverLetter) => void;
}

const STYLE_DESCRIPTIONS = {
  professional: 'Formal, structured, and traditional - ideal for corporate roles',
  enthusiastic: 'Energetic and passionate - shows genuine excitement for the opportunity',
  concise: 'Brief and to-the-point - highlights key qualifications efficiently',
  storytelling: 'Narrative-driven - weaves experience into a compelling story'
};

export default function CoverLetterEditor({ job, selectedCVBlocks, onSaved }: CoverLetterEditorProps) {
  const [content, setContent] = useState('');
  const [style, setStyle] = useState<CoverLetterStyle>('professional');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [savedLetter, setSavedLetter] = useState<GeneratedCoverLetter | null>(null);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Mock data for job requirements
  const keyRequirements = [
    '5+ years of experience in software development',
    'Strong proficiency in React and TypeScript',
    'Experience with RESTful APIs and backend integration',
    'Excellent communication and teamwork skills',
    'Bachelor\'s degree in Computer Science or related field'
  ];

  // Generate mock cover letter
  const generateCoverLetter = (selectedStyle: CoverLetterStyle) => {
    const company = job.company || 'the company';
    const role = job.role || 'this position';
    const location = job.location || 'your location';

    let opening = '';
    let whyCompany = '';
    let whyMe = '';
    let closing = '';

    switch (selectedStyle) {
      case 'professional':
        opening = `Dear Hiring Manager,\n\nI am writing to express my strong interest in the ${role} position at ${company}. With my extensive background in software engineering and proven track record of delivering high-quality solutions, I am confident that I would make a valuable addition to your team.`;
        whyCompany = `I have long admired ${company}'s commitment to innovation and excellence in the industry. Your company's focus on cutting-edge technology and collaborative work environment aligns perfectly with my professional values and career aspirations. The opportunity to contribute to ${company}'s mission while working ${location} is particularly appealing.`;
        whyMe = `Throughout my career, I have developed strong expertise in React, TypeScript, and full-stack development. I have successfully led projects that improved system performance by 40% and reduced deployment time by 60%. My experience in building scalable web applications and collaborating with cross-functional teams has prepared me well for the challenges of this role. I am particularly proud of my track record in mentoring junior developers and fostering a culture of continuous learning.`;
        closing = `I am excited about the possibility of bringing my technical expertise and passion for innovation to ${company}. I would welcome the opportunity to discuss how my background and skills align with your team's needs. Thank you for considering my application.\n\nSincerely,\n[Your Name]`;
        break;

      case 'enthusiastic':
        opening = `Dear Hiring Team,\n\nI couldn't be more excited to apply for the ${role} position at ${company}! As a passionate software engineer who thrives on solving complex problems, I've been following ${company}'s journey and I'm truly inspired by what you're building.`;
        whyCompany = `What really draws me to ${company} is your innovative approach to technology and your company culture that values creativity and collaboration. I've been particularly impressed by your recent projects and initiatives. The chance to work ${location} with a team that's pushing boundaries in the industry is a dream opportunity for me!`;
        whyMe = `I bring not just skills, but genuine enthusiasm for what I do. My experience with React and TypeScript has allowed me to build applications that users love, and I'm constantly exploring new technologies to stay at the cutting edge. I've led teams through challenging projects, always maintaining a positive attitude and focusing on solutions. My colleagues often describe me as the person who brings energy and fresh perspectives to every project.`;
        closing = `I would absolutely love the chance to contribute to ${company}'s success and grow alongside your talented team. Let's chat about how we can create something amazing together!\n\nLooking forward to connecting,\n[Your Name]`;
        break;

      case 'concise':
        opening = `Dear Hiring Manager,\n\nI am applying for the ${role} position at ${company}. My 5+ years of experience in software development and expertise in React/TypeScript make me an ideal candidate.`;
        whyCompany = `${company}'s reputation for innovation and technical excellence aligns with my career goals. The ${location} position offers the challenge and growth opportunity I seek.`;
        whyMe = `Key qualifications:\n• Expert-level proficiency in React, TypeScript, and modern web technologies\n• Proven track record: 40% performance improvement, 60% faster deployments\n• Strong leadership experience with cross-functional teams\n• Consistent delivery of scalable, maintainable solutions`;
        closing = `I'm confident I can contribute immediately to your team's success. I look forward to discussing this opportunity further.\n\nBest regards,\n[Your Name]`;
        break;

      case 'storytelling':
        opening = `Dear Hiring Manager,\n\nFive years ago, I wrote my first React component, and it changed everything. What started as curiosity evolved into a passion for building user experiences that make a difference. When I discovered the ${role} opening at ${company}, I knew this was where my journey should lead next.`;
        whyCompany = `I first learned about ${company} through your innovative products that caught the attention of the developer community. What struck me wasn't just the technology—it was the story behind it. Your commitment to solving real problems and your collaborative culture resonates with my own values. Working ${location} with a team that shares this vision represents the next chapter in my professional story.`;
        whyMe = `My path in software engineering has been one of continuous growth and meaningful impact. I remember the project where I first led a team—we were facing a critical performance issue, and through collaboration and innovative thinking, we not only solved it but improved performance by 40%. That experience taught me that great technology is built by great teams. Each project since has added a new chapter: scaling applications, mentoring developers, and always pushing to learn more.`;
        closing = `I see this role at ${company} as an opportunity to write the next exciting chapter—not just for me, but for the entire team. I'd love to share more of my story and learn about yours.\n\nWarm regards,\n[Your Name]`;
        break;
    }

    return `${opening}\n\n${whyCompany}\n\n${whyMe}\n\n${closing}`;
  };

  const handleGenerate = () => {
    setIsGenerating(true);

    // Simulate API call delay
    setTimeout(() => {
      const generatedContent = generateCoverLetter(style);
      setContent(generatedContent);
      setIsDirty(true);
      setIsGenerating(false);
    }, 1500);
  };

  const handleRegenerateSection = (section: 'opening' | 'company' | 'fit' | 'closing') => {
    setIsGenerating(true);

    // In a real implementation, this would call the API to regenerate just that section
    setTimeout(() => {
      alert(`Regenerating ${section} section... (This is a mock implementation)`);
      setIsGenerating(false);
    }, 1000);
  };

  const handleSave = () => {
    setIsSaving(true);

    // Simulate API call
    setTimeout(() => {
      const letter: GeneratedCoverLetter = {
        id: Math.floor(Math.random() * 10000),
        jobId: job.id,
        content: content,
        templateUsed: style,
        createdAt: new Date().toISOString()
      };

      setSavedLetter(letter);
      setLastSaved(new Date());
      setIsDirty(false);
      setIsSaving(false);

      if (onSaved) {
        onSaved(letter);
      }
    }, 800);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      alert('Cover letter copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy:', err);
      alert('Failed to copy to clipboard');
    }
  };

  const handleExportPDF = () => {
    // Mock implementation
    alert('PDF export would be implemented here. This would generate a properly formatted PDF document.');
  };

  // Update word and character counts
  const wordCount = content.trim().split(/\s+/).filter(w => w.length > 0).length;
  const charCount = content.length;

  // Auto-save effect (every 30 seconds if dirty)
  useEffect(() => {
    if (!isDirty || !content) return;

    const autoSaveTimer = setTimeout(() => {
      handleSave();
    }, 30000);

    return () => clearTimeout(autoSaveTimer);
  }, [content, isDirty]);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Cover Letter Editor</h2>
        <p className="text-sm text-gray-600 mt-1">
          Generate and customize your cover letter for this position
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Context & Controls */}
        <div className="lg:col-span-1 space-y-6">
          {/* Job Summary Card */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">Job Details</h3>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium text-gray-700">Role:</span>
                <p className="text-gray-900">{job.role || 'N/A'}</p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Company:</span>
                <p className="text-gray-900">{job.company || 'N/A'}</p>
              </div>
              <div>
                <span className="font-medium text-gray-700">Location:</span>
                <p className="text-gray-900">{job.location || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Key Requirements */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Key Requirements</h3>
            <ul className="space-y-1 text-xs text-gray-700">
              {keyRequirements.map((req, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Style Selector */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Writing Style</h3>
            <div className="space-y-2">
              {(['professional', 'enthusiastic', 'concise', 'storytelling'] as CoverLetterStyle[]).map((styleOption) => (
                <label key={styleOption} className="flex items-start cursor-pointer group">
                  <input
                    type="radio"
                    name="style"
                    value={styleOption}
                    checked={style === styleOption}
                    onChange={(e) => setStyle(e.target.value as CoverLetterStyle)}
                    className="mt-1 mr-3 text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <div className="font-medium text-sm text-gray-900 capitalize group-hover:text-blue-600">
                      {styleOption}
                    </div>
                    <div className="text-xs text-gray-600">
                      {STYLE_DESCRIPTIONS[styleOption]}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Generation Buttons */}
          <div className="space-y-3">
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors font-semibold"
            >
              {isGenerating ? 'Generating...' : content ? 'Regenerate Letter' : 'Generate Letter'}
            </button>

            {content && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-gray-700 mb-2">Regenerate Sections:</p>
                <button
                  onClick={() => handleRegenerateSection('opening')}
                  disabled={isGenerating}
                  className="w-full bg-gray-100 text-gray-700 py-2 px-3 rounded-md hover:bg-gray-200 disabled:bg-gray-50 transition-colors text-sm"
                >
                  Regenerate Opening
                </button>
                <button
                  onClick={() => handleRegenerateSection('company')}
                  disabled={isGenerating}
                  className="w-full bg-gray-100 text-gray-700 py-2 px-3 rounded-md hover:bg-gray-200 disabled:bg-gray-50 transition-colors text-sm"
                >
                  Regenerate "Why Company"
                </button>
                <button
                  onClick={() => handleRegenerateSection('fit')}
                  disabled={isGenerating}
                  className="w-full bg-gray-100 text-gray-700 py-2 px-3 rounded-md hover:bg-gray-200 disabled:bg-gray-50 transition-colors text-sm"
                >
                  Regenerate "Why Me"
                </button>
                <button
                  onClick={() => handleRegenerateSection('closing')}
                  disabled={isGenerating}
                  className="w-full bg-gray-100 text-gray-700 py-2 px-3 rounded-md hover:bg-gray-200 disabled:bg-gray-50 transition-colors text-sm"
                >
                  Regenerate Closing
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Editor */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
            {/* Editor Toolbar */}
            <div className="bg-gray-50 border-b border-gray-300 px-4 py-2 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    document.execCommand('bold', false);
                  }}
                  className="p-2 hover:bg-gray-200 rounded text-gray-700 text-sm font-semibold"
                  title="Bold"
                >
                  B
                </button>
                <button
                  onClick={() => {
                    document.execCommand('italic', false);
                  }}
                  className="p-2 hover:bg-gray-200 rounded text-gray-700 text-sm italic"
                  title="Italic"
                >
                  I
                </button>
                <div className="h-4 w-px bg-gray-300" />
                <button
                  onClick={() => {
                    document.execCommand('insertUnorderedList', false);
                  }}
                  className="p-2 hover:bg-gray-200 rounded text-gray-700 text-sm"
                  title="Bullet Points"
                >
                  •
                </button>
              </div>

              {/* Auto-save indicator */}
              <div className="text-xs text-gray-600">
                {isSaving ? (
                  <span className="text-blue-600">Saving...</span>
                ) : lastSaved ? (
                  <span>Last saved: {lastSaved.toLocaleTimeString()}</span>
                ) : isDirty ? (
                  <span className="text-amber-600">Unsaved changes</span>
                ) : null}
              </div>
            </div>

            {/* Editor Area */}
            <div className="p-6 bg-white">
              <textarea
                value={content}
                onChange={(e) => {
                  setContent(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="Generate a cover letter to get started, or write your own..."
                className="w-full h-[600px] border-none focus:outline-none focus:ring-0 resize-none font-serif text-base leading-relaxed text-gray-900"
                style={{ fontFamily: 'Georgia, serif', fontSize: '16px', lineHeight: '1.8' }}
              />
            </div>

            {/* Stats Bar */}
            <div className="bg-gray-50 border-t border-gray-300 px-4 py-2 flex items-center justify-between text-xs text-gray-600">
              <div className="flex gap-4">
                <span>{wordCount} words</span>
                <span>{charCount} characters</span>
              </div>
              {content && (
                <div className="text-xs text-gray-500">
                  {wordCount < 200 && <span className="text-amber-600">Consider adding more detail</span>}
                  {wordCount >= 200 && wordCount <= 400 && <span className="text-green-600">Good length</span>}
                  {wordCount > 400 && <span className="text-amber-600">Consider making it more concise</span>}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="bg-white border-t border-gray-300 px-4 py-4 flex gap-3">
              <button
                onClick={handleSave}
                disabled={!content || !isDirty || isSaving}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 transition-colors font-medium"
              >
                {isSaving ? 'Saving...' : 'Save Draft'}
              </button>
              <button
                onClick={handleExportPDF}
                disabled={!content}
                className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:text-gray-500 transition-colors font-medium"
              >
                Export PDF
              </button>
              <button
                onClick={handleCopy}
                disabled={!content}
                className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 disabled:bg-gray-300 disabled:text-gray-500 transition-colors font-medium"
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
