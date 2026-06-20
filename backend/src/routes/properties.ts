import { Router, Request, Response, NextFunction } from 'express';
import { prisma } from '../index';
import { AppError } from '../middleware/errorHandler';
import { requireAuth } from '../middleware/auth';
import { z } from 'zod';

const router = Router();
router.use(requireAuth);

const propertySchema = z.object({
  address: z.string().min(1),
  unitNumber: z.string().optional(),
});

// Create property
router.post('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const data = propertySchema.parse(req.body);
    const property = await prisma.property.create({
      data: { ...data, ownerId: req.user.id },
    });
    res.status(201).json({ status: 'success', data: { property } });
  } catch (error) {
    next(error);
  }
});

// Get user's properties
router.get('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const properties = await prisma.property.findMany({
      where: {
        OR: [
          { ownerId: req.user.id },
          { tenants: { some: { id: req.user.id } } },
        ],
      },
      include: {
        owner: { select: { id: true, name: true, email: true } },
        tenants: { select: { id: true, name: true, email: true } },
      },
    });
    res.json({ status: 'success', data: { properties } });
  } catch (error) {
    next(error);
  }
});

export const propertyRouter = router; 