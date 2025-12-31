import { useState, useEffect } from 'react';
import type { Job } from '../types/job';
import type { LegoBlock } from '../types/legoBlock';
import type { BlockSuggestion, GeneratedCV } from '../types/cv';

interface CVGeneratorProps {
  job: Job;
  onGenerated?: (cv: GeneratedCV) => void;
}

export default function CVGenerator({ job, onGenerated }: CVGeneratorProps) {
  const [suggestions, setSuggestions] = useState<BlockSuggestion[]>([]);
  const [selectedBlockIds, setSelectedBlockIds] = useState<number[]>([]);
  const [blockOrder, setBlockOrder] = useState<number[]>([]);
  const [customizations, setCustomizations] = useState<Record<number, string>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedCV, setGeneratedCV] = useState<GeneratedCV | null>(null);
  const [editingBlockId, setEditingBlockId] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // Mock data for suggestions - will be replaced with actual API call
  useEffect(() => {
    // Generate mock suggestions based on job data
    const mockSuggestions: BlockSuggestion[] = [
      {
        block: {
          id: 1,
          category: 'Experience',
          subcategory: 'Software Development',
          title: 'Senior Software Engineer at TechCorp',
          content: 'Led development of scalable microservices architecture serving 10M+ users. Implemented CI/CD pipelines reducing deployment time by 60%.',
          skills: ['Python', 'Docker', 'Kubernetes', 'AWS'],
          keywords: ['microservices', 'scalability', 'DevOps'],
          strengthLevel: 'essential',
          roleTypes: ['Software Engineer', 'Backend Engineer'],
          companyTypes: ['Tech Startup', 'Enterprise']
        },
        relevanceScore: 95,
        matchedSkills: ['Python', 'Docker', 'AWS'],
        reason: 'Strong match for backend engineering role with cloud infrastructure experience'
      },
      {
        block: {
          id: 2,
          category: 'Skills',
          subcategory: 'Programming Languages',
          title: 'Full-Stack Development',
          content: 'Expert in React, TypeScript, Node.js, Python. 5+ years building production applications.',
          skills: ['React', 'TypeScript', 'Node.js', 'Python'],
          keywords: ['full-stack', 'frontend', 'backend'],
          strengthLevel: 'essential',
          roleTypes: ['Software Engineer', 'Full-Stack Engineer'],
          companyTypes: ['Tech Startup', 'Enterprise']
        },
        relevanceScore: 88,
        matchedSkills: ['React', 'TypeScript', 'Python'],
        reason: 'Full-stack experience aligns with role requirements'
      },
      {
        block: {
          id: 3,
          category: 'Experience',
          subcategory: 'Leadership',
          title: 'Tech Lead - Mobile Platform',
          content: 'Managed team of 5 engineers. Designed and implemented new mobile architecture reducing crash rate by 80%.',
          skills: ['Team Leadership', 'Architecture Design', 'Mobile Development'],
          keywords: ['leadership', 'team management', 'mobile'],
          strengthLevel: 'strong',
          roleTypes: ['Tech Lead', 'Engineering Manager'],
          companyTypes: ['Tech Startup', 'Enterprise']
        },
        relevanceScore: 75,
        matchedSkills: ['Team Leadership'],
        reason: 'Leadership experience valuable for senior roles'
      },
      {
        block: {
          id: 4,
          category: 'Projects',
          subcategory: 'Open Source',
          title: 'Open Source Contributions',
          content: 'Active contributor to popular React libraries. Authored 3 npm packages with 50k+ downloads.',
          skills: ['React', 'JavaScript', 'TypeScript', 'Open Source'],
          keywords: ['open source', 'community', 'npm'],
          strengthLevel: 'good',
          roleTypes: ['Software Engineer', 'Frontend Engineer'],
          companyTypes: ['Tech Startup']
        },
        relevanceScore: 70,
        matchedSkills: ['React', 'TypeScript'],
        reason: 'Demonstrates initiative and community involvement'
      },
      {
        block: {
          id: 5,
          category: 'Education',
          subcategory: 'Formal Education',
          title: 'MS Computer Science',
          content: 'Master of Science in Computer Science, Stanford University. Focus on distributed systems and machine learning.',
          skills: ['Distributed Systems', 'Machine Learning', 'Algorithms'],
          keywords: ['education', 'CS', 'Stanford'],
          strengthLevel: 'strong',
          roleTypes: ['Software Engineer', 'Research Engineer'],
          companyTypes: ['Tech Startup', 'Enterprise', 'Research']
        },
        relevanceScore: 65,
        matchedSkills: [],
        reason: 'Strong educational background'
      },
      {
        block: {
          id: 6,
          category: 'Achievements',
          subcategory: 'Awards',
          title: 'Hackathon Winner',
          content: 'Won first place at TechCrunch Disrupt Hackathon 2023. Built AI-powered code review tool.',
          skills: ['AI/ML', 'Product Development', 'Innovation'],
          keywords: ['hackathon', 'award', 'innovation'],
          strengthLevel: 'good',
          roleTypes: ['Software Engineer'],
          companyTypes: ['Tech Startup']
        },
        relevanceScore: 60,
        matchedSkills: [],
        reason: 'Shows innovation and competitive achievement'
      }
    ];

    setSuggestions(mockSuggestions);
  }, [job]);

  // Parse skills from job (mock implementation)
  const parseJobSkills = (): string[] => {
    if (!job.notes) return [];
    // Simple skill extraction from notes
    const commonSkills = ['Python', 'React', 'TypeScript', 'Docker', 'AWS', 'Kubernetes', 'Node.js', 'SQL'];
    return commonSkills.filter(skill =>
      job.notes?.toLowerCase().includes(skill.toLowerCase()) ||
      job.role?.toLowerCase().includes(skill.toLowerCase())
    );
  };

  // Calculate match score
  const calculateMatchScore = (): number => {
    const jobSkills = parseJobSkills();
    const selectedBlocks = suggestions
      .filter(s => selectedBlockIds.includes(s.block.id))
      .map(s => s.block);

    const coveredSkills = new Set(
      selectedBlocks.flatMap(b => b.skills)
    );

    if (jobSkills.length === 0) return 0;
    const matchedCount = jobSkills.filter(skill =>
      Array.from(coveredSkills).some(cs => cs.toLowerCase() === skill.toLowerCase())
    ).length;

    return Math.round((matchedCount / jobSkills.length) * 100);
  };

  const handleAddBlock = (blockId: number) => {
    if (!selectedBlockIds.includes(blockId)) {
      setSelectedBlockIds([...selectedBlockIds, blockId]);
      setBlockOrder([...blockOrder, blockId]);
    }
  };

  const handleRemoveBlock = (blockId: number) => {
    setSelectedBlockIds(selectedBlockIds.filter(id => id !== blockId));
    setBlockOrder(blockOrder.filter(id => id !== blockId));
    // Remove customization if exists
    const newCustomizations = { ...customizations };
    delete newCustomizations[blockId];
    setCustomizations(newCustomizations);
  };

  const handleEditBlock = (blockId: number) => {
    const block = suggestions.find(s => s.block.id === blockId)?.block;
    if (block) {
      setEditingBlockId(blockId);
      setEditingText(customizations[blockId] || block.content);
    }
  };

  const handleSaveEdit = () => {
    if (editingBlockId !== null) {
      setCustomizations({
        ...customizations,
        [editingBlockId]: editingText
      });
      setEditingBlockId(null);
      setEditingText('');
    }
  };

  const handleCancelEdit = () => {
    setEditingBlockId(null);
    setEditingText('');
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    const newOrder = [...blockOrder];
    const draggedId = newOrder[draggedIndex];
    newOrder.splice(draggedIndex, 1);
    newOrder.splice(index, 0, draggedId);

    setBlockOrder(newOrder);
    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const handleGeneratePDF = async () => {
    setIsGenerating(true);

    // Mock PDF generation - would call actual API
    setTimeout(() => {
      const cv: GeneratedCV = {
        id: Date.now(),
        jobId: job.id,
        selectedBlocks: blockOrder,
        customizations,
        pdfPath: '/mock/cv.pdf',
        createdAt: new Date().toISOString()
      };

      setGeneratedCV(cv);
      setIsGenerating(false);

      if (onGenerated) {
        onGenerated(cv);
      }

      alert('CV PDF generated successfully! (Mock implementation)');
    }, 2000);
  };

  const handleSaveDraft = () => {
    alert('Draft saved! (Mock implementation)');
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset? All selections will be lost.')) {
      setSelectedBlockIds([]);
      setBlockOrder([]);
      setCustomizations({});
      setGeneratedCV(null);
    }
  };

  const getBlockById = (id: number): LegoBlock | undefined => {
    return suggestions.find(s => s.block.id === id)?.block;
  };

  const maxBlocks = 6;
  const matchScore = calculateMatchScore();
  const jobSkills = parseJobSkills();

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Generate CV for {job.role} at {job.company}
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column: Job Context (1/4) */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Job Context</h2>

              <div className="space-y-2">
                <div>
                  <p className="text-sm font-medium text-gray-500">Role</p>
                  <p className="text-sm text-gray-900">{job.role}</p>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-500">Company</p>
                  <p className="text-sm text-gray-900">{job.company}</p>
                </div>

                {job.location && (
                  <div>
                    <p className="text-sm font-medium text-gray-500">Location</p>
                    <p className="text-sm text-gray-900">{job.location}</p>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm font-medium text-gray-700 mb-2">Match Score</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        matchScore >= 80 ? 'bg-green-500' :
                        matchScore >= 60 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${matchScore}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-gray-900">{matchScore}%</span>
                </div>
              </div>

              {jobSkills.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">Parsed Skills</p>
                  <div className="flex flex-wrap gap-1">
                    {jobSkills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {job.notes && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">Requirements</p>
                  <p className="text-xs text-gray-600 line-clamp-6">{job.notes}</p>
                </div>
              )}
            </div>
          </div>

          {/* Middle Column: Block Selection (2/4) */}
          <div className="lg:col-span-2 space-y-4">
            {/* AI Suggestions */}
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Suggestions</h2>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {suggestions.map((suggestion) => (
                  <div
                    key={suggestion.block.id}
                    className="border border-gray-200 rounded-lg p-3 hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="text-sm font-medium text-gray-900">{suggestion.block.title}</h3>
                        <p className="text-xs text-gray-500 mt-1">
                          <span className="inline-block px-2 py-0.5 bg-gray-100 rounded text-xs">
                            {suggestion.block.category}
                          </span>
                        </p>
                      </div>
                      <button
                        onClick={() => handleAddBlock(suggestion.block.id)}
                        disabled={selectedBlockIds.includes(suggestion.block.id)}
                        className="ml-2 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      >
                        {selectedBlockIds.includes(suggestion.block.id) ? 'Added' : 'Add'}
                      </button>
                    </div>

                    {/* Relevance Score */}
                    <div className="mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full"
                            style={{ width: `${suggestion.relevanceScore}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-gray-600">{suggestion.relevanceScore}%</span>
                      </div>
                    </div>

                    {/* Matched Skills */}
                    {suggestion.matchedSkills.length > 0 && (
                      <div className="mb-2">
                        <div className="flex flex-wrap gap-1">
                          {suggestion.matchedSkills.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Reason */}
                    <p className="text-xs text-gray-600 italic">{suggestion.reason}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Blocks */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Selected Blocks</h2>
                <span className="text-sm text-gray-500">
                  {selectedBlockIds.length}/{maxBlocks} blocks
                </span>
              </div>

              {blockOrder.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">
                  No blocks selected. Add blocks from AI suggestions above.
                </p>
              ) : (
                <div className="space-y-2">
                  {blockOrder.map((blockId, index) => {
                    const block = getBlockById(blockId);
                    if (!block) return null;

                    return (
                      <div
                        key={blockId}
                        draggable
                        onDragStart={() => handleDragStart(index)}
                        onDragOver={(e) => handleDragOver(e, index)}
                        onDragEnd={handleDragEnd}
                        className={`border border-gray-200 rounded-lg p-3 cursor-move hover:border-blue-300 transition-colors ${
                          draggedIndex === index ? 'opacity-50' : ''
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-gray-400">☰</span>
                              <h3 className="text-sm font-medium text-gray-900">{block.title}</h3>
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              <span className="inline-block px-2 py-0.5 bg-gray-100 rounded">
                                {block.category}
                              </span>
                            </p>
                            {customizations[blockId] && (
                              <p className="text-xs text-blue-600 mt-1">✓ Customized</p>
                            )}
                          </div>
                          <div className="flex gap-2 ml-2">
                            <button
                              onClick={() => handleEditBlock(blockId)}
                              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200 transition-colors"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleRemoveBlock(blockId)}
                              className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded hover:bg-red-200 transition-colors"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <button
                className="mt-4 w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
              >
                Browse More Blocks
              </button>
            </div>
          </div>

          {/* Right Column: Preview & Actions (1/4) */}
          <div className="lg:col-span-1 space-y-4">
            {/* Mini Preview */}
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">CV Preview</h2>

              <div className="bg-gray-50 rounded p-3 text-xs space-y-2 max-h-64 overflow-y-auto">
                <div className="font-bold text-base text-gray-900">Your Name</div>
                <div className="text-gray-600">Contact Info</div>

                {blockOrder.length > 0 ? (
                  <div className="mt-3 space-y-3">
                    {blockOrder.map((blockId) => {
                      const block = getBlockById(blockId);
                      if (!block) return null;

                      return (
                        <div key={blockId} className="border-l-2 border-blue-500 pl-2">
                          <div className="font-medium text-gray-800">{block.title}</div>
                          <div className="text-gray-600 mt-1 line-clamp-2">
                            {customizations[blockId] || block.content}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-gray-400 text-center py-8">
                    Select blocks to preview
                  </div>
                )}
              </div>

              <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-700">
                <p className="font-medium">Blocks: {selectedBlockIds.length}/{maxBlocks}</p>
                <p>Match: {matchScore}%</p>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-white rounded-lg shadow p-4 space-y-3">
              <button
                onClick={handleGeneratePDF}
                disabled={isGenerating || selectedBlockIds.length === 0}
                className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isGenerating ? 'Generating...' : 'Generate PDF'}
              </button>

              <button
                onClick={handleSaveDraft}
                disabled={selectedBlockIds.length === 0}
                className="w-full py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                Save Draft
              </button>

              <button
                onClick={handleReset}
                disabled={selectedBlockIds.length === 0}
                className="w-full py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                Reset
              </button>
            </div>

            {generatedCV && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm font-medium text-green-800 mb-1">CV Generated!</p>
                <p className="text-xs text-green-700">
                  {new Date(generatedCV.createdAt).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {editingBlockId !== null && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">
                Edit Block: {getBlockById(editingBlockId)?.title}
              </h3>
            </div>

            <div className="p-6">
              <textarea
                value={editingText}
                onChange={(e) => setEditingText(e.target.value)}
                rows={10}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder="Edit the block content..."
              />
            </div>

            <div className="p-6 border-t border-gray-200 flex gap-3">
              <button
                onClick={handleSaveEdit}
                className="flex-1 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Changes
              </button>
              <button
                onClick={handleCancelEdit}
                className="flex-1 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
