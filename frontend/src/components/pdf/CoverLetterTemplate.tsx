import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';
import type { Job } from '../../types/job';

const styles = StyleSheet.create({
  page: {
    padding: 60,
    fontSize: 11,
    fontFamily: 'Helvetica',
  },
  header: {
    marginBottom: 30,
  },
  name: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  contactInfo: {
    fontSize: 10,
    color: '#555',
    marginBottom: 3,
  },
  date: {
    fontSize: 10,
    marginBottom: 30,
  },
  recipient: {
    fontSize: 11,
    marginBottom: 30,
  },
  recipientName: {
    fontWeight: 'bold',
    marginBottom: 3,
  },
  salutation: {
    fontSize: 11,
    marginBottom: 15,
  },
  paragraph: {
    fontSize: 11,
    lineHeight: 1.6,
    marginBottom: 15,
    textAlign: 'justify',
  },
  closing: {
    fontSize: 11,
    marginTop: 20,
    marginBottom: 40,
  },
  signature: {
    fontSize: 11,
    fontWeight: 'bold',
  },
});

export interface CoverLetterTemplateProps {
  name: string;
  email: string;
  phone: string;
  location: string;
  job: Job;
  content: string;
}

export const CoverLetterTemplate: React.FC<CoverLetterTemplateProps> = ({
  name,
  email,
  phone,
  location,
  job,
  content,
}) => {
  // Split content into paragraphs
  const paragraphs = content.split('\n\n').filter((p) => p.trim());

  // Format today's date
  const today = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        {/* Header with contact info */}
        <View style={styles.header}>
          <Text style={styles.name}>{name}</Text>
          <Text style={styles.contactInfo}>{email}</Text>
          <Text style={styles.contactInfo}>{phone}</Text>
          <Text style={styles.contactInfo}>{location}</Text>
        </View>

        {/* Date */}
        <Text style={styles.date}>{today}</Text>

        {/* Recipient */}
        <View style={styles.recipient}>
          <Text style={styles.recipientName}>Hiring Manager</Text>
          {job.company && <Text>{job.company}</Text>}
          {job.department && <Text>{job.department}</Text>}
        </View>

        {/* Salutation */}
        <Text style={styles.salutation}>Dear Hiring Manager,</Text>

        {/* Body paragraphs */}
        {paragraphs.map((paragraph, idx) => (
          <Text key={idx} style={styles.paragraph}>
            {paragraph}
          </Text>
        ))}

        {/* Closing */}
        <Text style={styles.closing}>Sincerely,</Text>
        <Text style={styles.signature}>{name}</Text>
      </Page>
    </Document>
  );
};
