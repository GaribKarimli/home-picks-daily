import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    image: z.string(),
    price: z.string(),
    amazonLink: z.string(),
    category: z.enum(['Kitchen Gadgets', 'Living Room Decor', 'Organization Hacks']),
    features: z.array(z.string()),
    rating: z.number().min(0).max(5),
    date: z.date(),
    description: z.string(),
  }),
});

export const collections = { posts };
