import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';
import type { LegoBlock } from '../../types/legoBlock';
import type { Job } from '../../types/job';

const styles = StyleSheet.create({
  page: {
    padding: 40,
    fontSize: 11,
    fontFamily: 'Helvetica',
  },
  header: {
    marginBottom: 20,
    borderBottom: '2 solid #000',
    paddingBottom: 10,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  contactInfo: {
    fontSize: 10,
    color: '#555',
  },
  section: {
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    textTransform: 'uppercase',
    borderBottom: '1 solid #333',
    paddingBottom: 4,
  },
  subsectionTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 6,
    marginTop: 8,
  },
  objective: {
    fontSize: 11,
    lineHeight: 1.4,
    marginBottom: 10,
  },
  bulletPoint: {
    fontSize: 10,
    lineHeight: 1.5,
    marginBottom: 6,
    marginLeft: 15,
    textAlign: 'justify',
  },
  skillsList: {
    fontSize: 10,
    lineHeight: 1.4,
  },
});

export interface CVTemplateProps {
  name: string;
  email: string;
  phone: string;
  location: string;
  job: Job;
  selectedBlocks: LegoBlock[];
}

export const CVTemplate: React.FC<CVTemplateProps> = ({
  name,
  email,
  phone,
  location,
  job,
  selectedBlocks,
}) => {
  // Group blocks by category
  const blocksByCategory = selectedBlocks.reduce((acc, block) => {
    if (!acc[block.category]) {
      acc[block.category] = [];
    }
    acc[block.category].push(block);
    return acc;
  }, {} as Record<string, LegoBlock[]>);

  // Extract unique skills from blocks
  const allSkills = new Set<string>();
  selectedBlocks.forEach((block) => {
    if (block.skills) {
      block.skills.forEach((skill) => allSkills.add(skill));
    }
  });
  const skillsArray = Array.from(allSkills).sort();

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.name}>{name}</Text>
          <Text style={styles.contactInfo}>
            {email} • {phone} • {location}
          </Text>
        </View>

        {/* Objective */}
        {job.role && job.company && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Objective</Text>
            <Text style={styles.objective}>
              Seeking the {job.role} position at {job.company} where I can leverage my proven track
              record of delivering high-impact technical solutions and driving innovation.
            </Text>
          </View>
        )}

        {/* Professional Experience - Grouped by Category */}
        {Object.entries(blocksByCategory).map(([category, blocks]) => (
          <View key={category} style={styles.section}>
            <Text style={styles.sectionTitle}>{category}</Text>
            {blocks.map((block, idx) => (
              <View key={idx}>
                <Text style={styles.subsectionTitle}>{block.title}</Text>
                <Text style={styles.bulletPoint}>• {block.content}</Text>
              </View>
            ))}
          </View>
        ))}

        {/* Technical Skills */}
        {skillsArray.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Technical Skills</Text>
            <Text style={styles.skillsList}>{skillsArray.join(' • ')}</Text>
          </View>
        )}
      </Page>
    </Document>
  );
};
