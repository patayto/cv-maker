import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';

// Register fonts (optional - uses default if not provided)
// You can add custom fonts here for better typography

// PDF Styles matching Patrick Laverty CV format
const styles = StyleSheet.create({
  page: {
    fontFamily: 'Helvetica',
    fontSize: 11,
    paddingTop: 35,
    paddingBottom: 35,
    paddingHorizontal: 45,
    lineHeight: 1.3,
    color: '#000000',
  },
  header: {
    textAlign: 'center',
    marginBottom: 20,
  },
  name: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#2c3e50',
  },
  contactInfo: {
    fontSize: 10,
    color: '#333333',
    lineHeight: 1.4,
  },
  section: {
    marginTop: 18,
    marginBottom: 10,
  },
  sectionHeader: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2c3e50',
    borderBottomWidth: 1,
    borderBottomColor: '#2c3e50',
    paddingBottom: 2,
    marginBottom: 10,
  },
  jobHeader: {
    marginBottom: 8,
    marginTop: 12,
  },
  companyTitle: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  jobDetails: {
    fontSize: 10,
    fontStyle: 'italic',
    marginTop: 2,
    color: '#666666',
  },
  bulletPoint: {
    marginBottom: 6,
    paddingLeft: 15,
    flexDirection: 'row',
  },
  bulletMarker: {
    width: 15,
    marginLeft: -15,
  },
  bulletText: {
    flex: 1,
    fontSize: 11,
    lineHeight: 1.25,
  },
  summary: {
    marginBottom: 12,
    fontSize: 11,
    lineHeight: 1.25,
  },
  skillsGrid: {
    display: 'flex',
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  skillCategory: {
    width: '33%',
    marginBottom: 6,
  },
  skillCategoryLabel: {
    fontSize: 10,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  skillCategoryItems: {
    fontSize: 10,
    color: '#333333',
  },
});

export interface CVData {
  // Personal Info
  name: string;
  email: string;
  phone?: string;
  location?: string;
  linkedIn?: string;
  github?: string;

  // Sections
  professionalSummary?: string;
  technicalSkills?: {
    languages?: string[];
    mlAi?: string[];
    cloudInfra?: string[];
    other?: string[];
  };

  // Experience blocks
  experienceBlocks: {
    company: string;
    location: string;
    text: string;
  }[];

  // Personal Projects (optional)
  personalProjects?: string;

  // Education
  education?: {
    degree: string;
    institution: string;
    grade?: string;
    date: string;
  }[];
}

interface CVDocumentProps {
  data: CVData;
}

export default function CVDocument({ data }: CVDocumentProps) {
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.name}>{data.name}</Text>
          <View style={styles.contactInfo}>
            <Text>
              {data.email}
              {data.phone && ` | ${data.phone}`}
              {data.location && ` | ${data.location}`}
            </Text>
            {(data.linkedIn || data.github) && (
              <Text>
                {data.linkedIn && data.linkedIn}
                {data.linkedIn && data.github && ' | '}
                {data.github && data.github}
              </Text>
            )}
          </View>
        </View>

        {/* Professional Summary */}
        {data.professionalSummary && (
          <View style={styles.section}>
            <Text style={styles.sectionHeader}>PROFESSIONAL SUMMARY</Text>
            <Text style={styles.summary}>{data.professionalSummary}</Text>
          </View>
        )}

        {/* Technical Skills */}
        {data.technicalSkills && (
          <View style={styles.section}>
            <Text style={styles.sectionHeader}>TECHNICAL SKILLS</Text>
            <View style={styles.skillsGrid}>
              {data.technicalSkills.languages && data.technicalSkills.languages.length > 0 && (
                <View style={styles.skillCategory}>
                  <Text style={styles.skillCategoryLabel}>Languages:</Text>
                  <Text style={styles.skillCategoryItems}>
                    {data.technicalSkills.languages.join(', ')}
                  </Text>
                </View>
              )}
              {data.technicalSkills.mlAi && data.technicalSkills.mlAi.length > 0 && (
                <View style={styles.skillCategory}>
                  <Text style={styles.skillCategoryLabel}>ML/AI:</Text>
                  <Text style={styles.skillCategoryItems}>
                    {data.technicalSkills.mlAi.join(', ')}
                  </Text>
                </View>
              )}
              {data.technicalSkills.cloudInfra && data.technicalSkills.cloudInfra.length > 0 && (
                <View style={styles.skillCategory}>
                  <Text style={styles.skillCategoryLabel}>Cloud/Infra:</Text>
                  <Text style={styles.skillCategoryItems}>
                    {data.technicalSkills.cloudInfra.join(', ')}
                  </Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Professional Experience */}
        {data.experienceBlocks && data.experienceBlocks.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionHeader}>PROFESSIONAL EXPERIENCE</Text>

            {/* Group blocks by company */}
            {(() => {
              // Group experience blocks by company
              const groupedBlocks = data.experienceBlocks.reduce((acc, block) => {
                const key = `${block.company}|${block.location}`;
                if (!acc[key]) {
                  acc[key] = {
                    company: block.company,
                    location: block.location,
                    bullets: []
                  };
                }
                acc[key].bullets.push(block.text);
                return acc;
              }, {} as Record<string, { company: string; location: string; bullets: string[] }>);

              // Render grouped blocks
              return Object.values(groupedBlocks).map((group, idx) => (
                <View key={idx}>
                  <View style={styles.jobHeader}>
                    <Text style={styles.companyTitle}>{group.company}</Text>
                    <Text style={styles.jobDetails}>{group.location}</Text>
                  </View>

                  {group.bullets.map((bullet, bulletIdx) => (
                    <View key={bulletIdx} style={styles.bulletPoint}>
                      <Text style={styles.bulletMarker}>•</Text>
                      <Text style={styles.bulletText}>{bullet}</Text>
                    </View>
                  ))}
                </View>
              ));
            })()}
          </View>
        )}

        {/* Personal Projects */}
        {data.personalProjects && (
          <View style={styles.section}>
            <Text style={styles.sectionHeader}>PERSONAL PROJECTS</Text>
            <Text style={styles.summary}>{data.personalProjects}</Text>
          </View>
        )}

        {/* Education */}
        {data.education && data.education.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionHeader}>EDUCATION</Text>
            {data.education.map((edu, idx) => (
              <View key={idx} style={{ marginBottom: 6 }}>
                <Text style={styles.companyTitle}>{edu.degree}</Text>
                <Text style={styles.jobDetails}>
                  {edu.institution}
                  {edu.grade && ` | ${edu.grade}`}
                  {edu.date && ` | ${edu.date}`}
                </Text>
              </View>
            ))}
          </View>
        )}
      </Page>
    </Document>
  );
}
