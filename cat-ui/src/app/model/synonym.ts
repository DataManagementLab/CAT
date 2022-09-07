export interface Synonym {
  meaning: string;
  definition: string;
  type: string;
  lemmas: Synonym[];
}
