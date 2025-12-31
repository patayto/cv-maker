export interface LegoBlock {
  id: number;
  category: string;
  subcategory?: string;
  title: string;
  content: string;
  skills: string[];
  keywords: string[];
  strengthLevel: 'essential' | 'strong' | 'good';
  roleTypes: string[];
  companyTypes: string[];
}
