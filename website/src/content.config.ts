import { defineCollection, z } from 'astro:content';

const stories = defineCollection({
  type: 'data',
  schema: z.object({
    id: z.string(),
    title: z.string(),
    description: z.string().optional(),
    date: z.string().optional(),
    duration: z.string().optional(),
    cover: z.string(),
    audio: z.string(),
    content: z.string(),
  }),
});

export const collections = { stories };
