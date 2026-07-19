export interface Ingredient {
  qty: number | null;
  unit: string | null;
  item: string;
  note: string | null;
}

export interface Recipe {
  id: string;
  week: number;
  year: number;
  date: string;
  theme: string;
  title: string;
  dish: string;
  subreddit: string;
  track: string | null;
  redditUrl: string;
  sourceUrl: string | null;
  description: string;
  image: string;
  gallery: string[];
  servings: number;
  ingredients: Ingredient[];
  steps: string[];
  tags: string[];
  notes: string | null;
  photoOnly: boolean;
}
