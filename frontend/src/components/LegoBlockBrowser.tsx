import { useState, useEffect, useMemo } from 'react';
import type { LegoBlock } from '../types/legoBlock';

interface LegoBlockBrowserProps {
  onSelectBlock?: (block: LegoBlock) => void;
  selectedBlocks?: number[]; // IDs of already selected blocks
  filterBySkills?: string[]; // Pre-filter by skills (from job parsing)
}

// Mock data for development
const mockBlocks: LegoBlock[] = [
  {
    id: 1,
    category: 'System Architecture',
    subcategory: 'Cloud Infrastructure',
    title: 'Designed multi-region cloud architecture for global expansion',
    content: 'Led the design and implementation of a multi-region AWS infrastructure supporting 50M+ users across 3 continents. Architected auto-scaling systems, CDN distribution, and regional failover mechanisms. Reduced latency by 60% for international users while maintaining 99.99% uptime SLA.',
    skills: ['AWS', 'System Design', 'Cloud Architecture', 'Auto-scaling', 'CDN'],
    keywords: ['multi-region', 'scalability', 'AWS', 'global', 'infrastructure'],
    strengthLevel: 'essential',
    roleTypes: ['Senior Engineer', 'Staff Engineer', 'Principal Engineer', 'Engineering Manager'],
    companyTypes: ['Tech Startup', 'Enterprise', 'SaaS'],
  },
  {
    id: 2,
    category: 'ML & Data Science',
    subcategory: 'Recommendation Systems',
    title: 'Built ML recommendation engine increasing user engagement by 40%',
    content: 'Designed and deployed a collaborative filtering recommendation system using Python, scikit-learn, and TensorFlow. Processed 100M+ user interactions daily to generate personalized recommendations. Implemented A/B testing framework to measure impact, resulting in 40% increase in user engagement and 25% boost in conversion rates.',
    skills: ['Python', 'TensorFlow', 'Machine Learning', 'scikit-learn', 'A/B Testing', 'Data Pipeline'],
    keywords: ['recommendation', 'ML', 'personalization', 'engagement', 'collaborative filtering'],
    strengthLevel: 'essential',
    roleTypes: ['ML Engineer', 'Data Scientist', 'Senior Engineer'],
    companyTypes: ['Tech Startup', 'E-commerce', 'Social Media'],
  },
  {
    id: 3,
    category: 'Scale & Performance',
    subcategory: 'Database Optimization',
    title: 'Optimized database queries reducing response time by 80%',
    content: 'Identified and resolved critical performance bottlenecks in PostgreSQL database serving 10M+ daily queries. Implemented query optimization, proper indexing strategies, and connection pooling. Introduced read replicas and caching layer with Redis. Reduced average API response time from 2s to 400ms.',
    skills: ['PostgreSQL', 'SQL Optimization', 'Redis', 'Database Design', 'Performance Tuning'],
    keywords: ['performance', 'optimization', 'database', 'scaling', 'caching'],
    strengthLevel: 'strong',
    roleTypes: ['Backend Engineer', 'Senior Engineer', 'Database Engineer'],
    companyTypes: ['Tech Startup', 'Enterprise', 'SaaS'],
  },
  {
    id: 4,
    category: 'Cost Optimization',
    subcategory: 'Cloud Cost Management',
    title: 'Reduced AWS infrastructure costs by $500K annually',
    content: 'Conducted comprehensive audit of AWS infrastructure and identified cost optimization opportunities. Implemented automated rightsizing of EC2 instances, migrated workloads to Spot instances where appropriate, and optimized S3 storage classes. Set up cost monitoring dashboards and alerts. Achieved 45% reduction in annual cloud spend ($500K savings) while improving performance.',
    skills: ['AWS', 'Cost Optimization', 'FinOps', 'Infrastructure Management', 'CloudWatch'],
    keywords: ['cost reduction', 'AWS', 'optimization', 'efficiency', 'cloud spend'],
    strengthLevel: 'strong',
    roleTypes: ['Senior Engineer', 'Staff Engineer', 'Platform Engineer', 'Engineering Manager'],
    companyTypes: ['Tech Startup', 'Enterprise', 'SaaS'],
  },
  {
    id: 5,
    category: 'Technical Leadership',
    subcategory: 'Team Management',
    title: 'Led engineering team of 8 delivering product from 0 to 1',
    content: 'Managed cross-functional team of 8 engineers building a new B2B SaaS product. Established engineering processes, code review standards, and CI/CD pipeline. Mentored 3 junior engineers who were promoted during my tenure. Successfully delivered MVP in 6 months and achieved $2M ARR within first year. Built strong team culture focused on ownership and quality.',
    skills: ['Engineering Management', 'Team Leadership', 'Mentoring', 'Process Design', 'Product Development'],
    keywords: ['leadership', 'management', 'team building', 'mentoring', '0 to 1'],
    strengthLevel: 'essential',
    roleTypes: ['Engineering Manager', 'Senior Engineer', 'Tech Lead'],
    companyTypes: ['Tech Startup', 'SaaS'],
  },
  {
    id: 6,
    category: 'Cross-Functional',
    subcategory: 'Product Collaboration',
    title: 'Partnered with product team to define technical roadmap',
    content: 'Worked closely with Product Managers and Designers to translate business requirements into technical solutions. Led technical discovery sessions, provided effort estimates, and proposed alternative approaches balancing speed and quality. Successfully delivered 15+ features on time with high quality bar. Established feedback loop improving product-engineering collaboration.',
    skills: ['Product Management', 'Stakeholder Communication', 'Technical Planning', 'Agile'],
    keywords: ['cross-functional', 'product', 'collaboration', 'roadmap', 'stakeholder'],
    strengthLevel: 'good',
    roleTypes: ['Senior Engineer', 'Tech Lead', 'Engineering Manager'],
    companyTypes: ['Tech Startup', 'Enterprise', 'SaaS'],
  },
  {
    id: 7,
    category: 'DevOps',
    subcategory: 'CI/CD',
    title: 'Implemented comprehensive CI/CD pipeline reducing deployment time by 75%',
    content: 'Built automated CI/CD pipeline using GitHub Actions and Docker. Implemented automated testing (unit, integration, e2e), security scanning, and gradual rollout strategies. Set up infrastructure-as-code with Terraform. Reduced deployment time from 2 hours to 30 minutes while increasing deployment frequency from weekly to daily. Zero-downtime deployments became the norm.',
    skills: ['CI/CD', 'GitHub Actions', 'Docker', 'Terraform', 'DevOps', 'Automation'],
    keywords: ['automation', 'deployment', 'CI/CD', 'infrastructure', 'DevOps'],
    strengthLevel: 'strong',
    roleTypes: ['Senior Engineer', 'DevOps Engineer', 'Platform Engineer'],
    companyTypes: ['Tech Startup', 'Enterprise', 'SaaS'],
  },
  {
    id: 8,
    category: 'Full-Stack',
    subcategory: 'Modern Web Development',
    title: 'Built responsive web application using React and Node.js',
    content: 'Developed full-stack application using React with TypeScript for frontend and Node.js with Express for backend. Implemented modern patterns including hooks, context API, and server-side rendering. Built RESTful APIs with proper authentication and authorization. Achieved 95+ Lighthouse score for performance and accessibility. Application serves 100K+ monthly active users.',
    skills: ['React', 'TypeScript', 'Node.js', 'Express', 'REST API', 'Frontend Development', 'Backend Development'],
    keywords: ['full-stack', 'React', 'Node.js', 'web development', 'TypeScript'],
    strengthLevel: 'essential',
    roleTypes: ['Full-Stack Engineer', 'Frontend Engineer', 'Backend Engineer', 'Senior Engineer'],
    companyTypes: ['Tech Startup', 'SaaS', 'E-commerce'],
  },
  {
    id: 9,
    category: 'Innovation',
    subcategory: 'New Technology Adoption',
    title: 'Pioneered adoption of GraphQL improving frontend development velocity',
    content: 'Researched and championed migration from REST to GraphQL for API layer. Built proof-of-concept, documented benefits, and secured buy-in from leadership. Led migration effort training team of 12 engineers. Improved frontend development velocity by 40% through better data fetching patterns and reduced over-fetching. GraphQL adoption became standard across the organization.',
    skills: ['GraphQL', 'API Design', 'Technology Evaluation', 'Change Management', 'Documentation'],
    keywords: ['innovation', 'GraphQL', 'API', 'technology adoption', 'migration'],
    strengthLevel: 'good',
    roleTypes: ['Senior Engineer', 'Staff Engineer', 'Tech Lead'],
    companyTypes: ['Tech Startup', 'SaaS'],
  },
  {
    id: 10,
    category: 'Technical Skills',
    subcategory: 'Programming Languages',
    title: 'Expert in Python, JavaScript/TypeScript, and Go',
    content: 'Proficient in multiple programming languages with deep expertise in Python (8+ years), JavaScript/TypeScript (7+ years), and Go (3+ years). Built production systems in all three languages. Contributed to open-source projects. Stay current with language evolution and best practices. Can pick up new languages quickly as demonstrated by learning Rust for performance-critical services.',
    skills: ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Programming'],
    keywords: ['programming', 'Python', 'JavaScript', 'Go', 'polyglot'],
    strengthLevel: 'essential',
    roleTypes: ['Software Engineer', 'Senior Engineer', 'Staff Engineer'],
    companyTypes: ['Tech Startup', 'Enterprise', 'SaaS'],
  },
];

// Category structure with counts
interface CategoryNode {
  name: string;
  count: number;
  subcategories?: { [key: string]: number };
}

export default function LegoBlockBrowser({
  onSelectBlock,
  selectedBlocks = [],
  filterBySkills = [],
}: LegoBlockBrowserProps) {
  const [blocks] = useState<LegoBlock[]>(mockBlocks);
  const [isLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [skillFilter, setSkillFilter] = useState<string[]>(filterBySkills);
  const [roleTypeFilter, setRoleTypeFilter] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Initialize skill filter from props
  useEffect(() => {
    if (filterBySkills.length > 0) {
      setSkillFilter(filterBySkills);
    }
  }, [filterBySkills]);

  // Build category tree with counts
  const categoryTree = useMemo(() => {
    const tree: { [key: string]: CategoryNode } = {};

    blocks.forEach((block) => {
      if (!tree[block.category]) {
        tree[block.category] = {
          name: block.category,
          count: 0,
          subcategories: {},
        };
      }
      tree[block.category].count++;

      if (block.subcategory) {
        if (!tree[block.category].subcategories![block.subcategory]) {
          tree[block.category].subcategories![block.subcategory] = 0;
        }
        tree[block.category].subcategories![block.subcategory]++;
      }
    });

    return tree;
  }, [blocks]);

  // Get all unique skills for filter
  const allSkills = useMemo(() => {
    const skillSet = new Set<string>();
    blocks.forEach((block) => {
      block.skills.forEach((skill) => skillSet.add(skill));
    });
    return Array.from(skillSet).sort();
  }, [blocks]);

  // Get all unique role types
  const allRoleTypes = useMemo(() => {
    const roleSet = new Set<string>();
    blocks.forEach((block) => {
      block.roleTypes.forEach((role) => roleSet.add(role));
    });
    return Array.from(roleSet).sort();
  }, [blocks]);

  // Filter blocks based on all criteria
  const filteredBlocks = useMemo(() => {
    return blocks.filter((block) => {
      // Category filter
      if (selectedCategory && block.category !== selectedCategory) {
        return false;
      }

      // Search query filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesTitle = block.title.toLowerCase().includes(query);
        const matchesContent = block.content.toLowerCase().includes(query);
        const matchesKeywords = block.keywords.some((kw) =>
          kw.toLowerCase().includes(query)
        );
        if (!matchesTitle && !matchesContent && !matchesKeywords) {
          return false;
        }
      }

      // Skill filter
      if (skillFilter.length > 0) {
        const hasSkill = skillFilter.some((skill) =>
          block.skills.includes(skill)
        );
        if (!hasSkill) {
          return false;
        }
      }

      // Role type filter
      if (roleTypeFilter) {
        if (!block.roleTypes.includes(roleTypeFilter)) {
          return false;
        }
      }

      return true;
    });
  }, [blocks, selectedCategory, searchQuery, skillFilter, roleTypeFilter]);

  const handleSelectBlock = (block: LegoBlock) => {
    if (onSelectBlock) {
      onSelectBlock(block);
    }
  };

  const isBlockSelected = (blockId: number) => {
    return selectedBlocks.includes(blockId);
  };

  const toggleSkillFilter = (skill: string) => {
    if (skillFilter.includes(skill)) {
      setSkillFilter(skillFilter.filter((s) => s !== skill));
    } else {
      setSkillFilter([...skillFilter, skill]);
    }
  };

  const clearFilters = () => {
    setSelectedCategory('');
    setSearchQuery('');
    setSkillFilter([]);
    setRoleTypeFilter('');
  };

  const strengthColors = {
    essential: 'bg-green-100 text-green-800 border-green-300',
    strong: 'bg-blue-100 text-blue-800 border-blue-300',
    good: 'bg-gray-100 text-gray-800 border-gray-300',
  };

  const strengthLabels = {
    essential: 'Essential',
    strong: 'Strong',
    good: 'Good',
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading blocks...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } transition-all duration-300 bg-white border-r border-gray-200 overflow-hidden`}
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Categories</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <button
            onClick={() => setSelectedCategory('')}
            className={`w-full text-left px-3 py-2 rounded-md mb-2 transition-colors ${
              selectedCategory === ''
                ? 'bg-blue-100 text-blue-900 font-medium'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            All Categories ({blocks.length})
          </button>

          <div className="space-y-1">
            {Object.entries(categoryTree).map(([category, node]) => (
              <button
                key={category}
                onClick={() =>
                  setSelectedCategory(
                    selectedCategory === category ? '' : category
                  )
                }
                className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                  selectedCategory === category
                    ? 'bg-blue-100 text-blue-900 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="text-sm">{category}</span>
                  <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
                    {node.count}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto p-6">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {!sidebarOpen && (
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    ☰
                  </button>
                )}
                <h1 className="text-2xl font-bold text-gray-900">
                  CV Lego Blocks
                </h1>
              </div>
              {(selectedCategory ||
                searchQuery ||
                skillFilter.length > 0 ||
                roleTypeFilter) && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Clear all filters
                </button>
              )}
            </div>

            {/* Search Bar */}
            <div className="bg-white rounded-lg shadow p-4 mb-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title, content, or keywords..."
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Filter by Skills
                  {skillFilter.length > 0 && (
                    <span className="ml-2 text-xs text-gray-500">
                      ({skillFilter.length} selected)
                    </span>
                  )}
                </label>
                <div className="flex flex-wrap gap-2">
                  {allSkills.slice(0, 20).map((skill) => (
                    <button
                      key={skill}
                      onClick={() => toggleSkillFilter(skill)}
                      className={`px-3 py-1 rounded-full text-sm transition-colors ${
                        skillFilter.includes(skill)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {skill}
                    </button>
                  ))}
                  {allSkills.length > 20 && (
                    <span className="px-3 py-1 text-sm text-gray-500">
                      +{allSkills.length - 20} more
                    </span>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Filter by Role Type
                </label>
                <select
                  value={roleTypeFilter}
                  onChange={(e) => setRoleTypeFilter(e.target.value)}
                  className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Role Types</option>
                  {allRoleTypes.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Results Count */}
          <div className="mb-4 text-sm text-gray-600">
            Showing {filteredBlocks.length} of {blocks.length} blocks
          </div>

          {/* Block Grid */}
          {filteredBlocks.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500">
                No blocks found matching your criteria. Try adjusting your
                filters.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {filteredBlocks.map((block) => (
                <div
                  key={block.id}
                  className={`bg-white rounded-lg shadow hover:shadow-lg transition-all p-6 ${
                    isBlockSelected(block.id)
                      ? 'ring-2 ring-blue-500 bg-blue-50'
                      : ''
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="flex items-start gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 flex-1">
                          {block.title}
                        </h3>
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium border ${
                            strengthColors[block.strengthLevel]
                          }`}
                        >
                          {strengthLabels[block.strengthLevel]}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                          {block.category}
                        </span>
                        {block.subcategory && (
                          <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs">
                            {block.subcategory}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <p className="text-gray-700 mb-4 leading-relaxed">
                    {block.content}
                  </p>

                  <div className="mb-3">
                    <div className="flex flex-wrap gap-1.5">
                      {block.skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex justify-between items-center pt-3 border-t border-gray-200">
                    <div className="text-xs text-gray-500">
                      {block.roleTypes.slice(0, 3).join(', ')}
                      {block.roleTypes.length > 3 &&
                        ` +${block.roleTypes.length - 3} more`}
                    </div>
                    <button
                      onClick={() => handleSelectBlock(block)}
                      className={`px-4 py-2 rounded-md font-medium transition-colors ${
                        isBlockSelected(block.id)
                          ? 'bg-green-600 text-white hover:bg-green-700'
                          : 'bg-blue-600 text-white hover:bg-blue-700'
                      }`}
                    >
                      {isBlockSelected(block.id) ? '✓ Selected' : 'Add to CV'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
