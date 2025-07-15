export async function fetchCriteriaList(): Promise<string[]> {
  const res = await fetch('http://localhost:8000/criteria');
  if (!res.ok) throw new Error('Failed to fetch criteria list');
  return res.json();
}

export async function fetchCriteria(loanType: string): Promise<any> {
  const res = await fetch(`http://localhost:8000/criteria/${loanType}`);
  if (!res.ok) throw new Error('Failed to fetch criteria');
  return res.json();
} 