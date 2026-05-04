import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    image: z.string(),
    price: z.string(),
    amazonLink: z.string(),
    niche: z.enum(['home-decor', 'tech-gadgets', 'fitness-equipment', 'kitchen-essentials']),
    category: z.string(),
    features: z.array(z.string()),
    rating: z.number().min(0).max(5),
    reviews: z.number().default(0),
    date: z.date(),
    description: z.string(),
    trending: z.boolean().default(false),
  }),
});

export const collections = { posts };
