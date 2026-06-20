import { Router, Request, Response, NextFunction } from 'express';
import { prisma } from '../index';
import { AppError } from '../middleware/errorHandler';
import { requireAuth } from '../middleware/auth';
import { z } from 'zod';

const router = Router();

// Apply auth middleware to all routes
router.use(requireAuth);

// Validation schemas
const createRepairSchema = z.object({
  title: z.string().min(3),
  description: z.string().min(10),
  propertyId: z.string().uuid(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'EMERGENCY']).optional(),
});

const updateRepairSchema = z.object({
  title: z.string().min(3).optional(),
  description: z.string().min(10).optional(),
  status: z.enum(['PENDING', 'ANALYZING', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']).optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'EMERGENCY']).optional(),
  assignedToId: z.string().uuid().optional(),
});

// Create repair request
router.post('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { title, description, propertyId, priority } = createRepairSchema.parse(req.body);

    // Verify user has access to the property
    const property = await prisma.property.findFirst({
      where: {
        id: propertyId,
        OR: [
          { ownerId: req.user.id },
          { tenants: { some: { id: req.user.id } } },
        ],
      },
    });

    if (!property) {
      throw new AppError(403, 'You do not have access to this property');
    }

    const repair = await prisma.repairRequest.create({
      data: {
        title,
        description,
        propertyId,
        requestedById: req.user.id,
        priority: priority || 'MEDIUM',
      },
      include: {
        property: true,
        requestedBy: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
      },
    });

    // TODO: Trigger AI agent to analyze the repair request

    res.status(201).json({
      status: 'success',
      data: { repair },
    });
  } catch (error) {
    next(error);
  }
});

// Get all repair requests for a user
router.get('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const repairs = await prisma.repairRequest.findMany({
      where: {
        OR: [
          { requestedById: req.user.id },
          { assignedToId: req.user.id },
          {
            property: {
              OR: [
                { ownerId: req.user.id },
                { tenants: { some: { id: req.user.id } } },
              ],
            },
          },
        ],
      },
      include: {
        property: true,
        requestedBy: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
        assignedTo: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
        messages: {
          orderBy: { createdAt: 'desc' },
          take: 1,
        },
      },
      orderBy: { createdAt: 'desc' },
    });

    res.json({
      status: 'success',
      data: { repairs },
    });
  } catch (error) {
    next(error);
  }
});

// Get single repair request
router.get('/:id', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const repair = await prisma.repairRequest.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { requestedById: req.user.id },
          { assignedToId: req.user.id },
          {
            property: {
              OR: [
                { ownerId: req.user.id },
                { tenants: { some: { id: req.user.id } } },
              ],
            },
          },
        ],
      },
      include: {
        property: true,
        requestedBy: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
        assignedTo: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
        messages: {
          orderBy: { createdAt: 'asc' },
        },
      },
    });

    if (!repair) {
      throw new AppError(404, 'Repair request not found');
    }

    res.json({
      status: 'success',
      data: { repair },
    });
  } catch (error) {
    next(error);
  }
});

// Update repair request
router.patch('/:id', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const updates = updateRepairSchema.parse(req.body);

    // Verify user has permission to update
    const existingRepair = await prisma.repairRequest.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { requestedById: req.user.id },
          { assignedToId: req.user.id },
          {
            property: {
              ownerId: req.user.id,
            },
          },
        ],
      },
    });

    if (!existingRepair) {
      throw new AppError(404, 'Repair request not found or you do not have permission to update it');
    }

    const repair = await prisma.repairRequest.update({
      where: { id: req.params.id },
      data: updates,
      include: {
        property: true,
        requestedBy: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
        assignedTo: {
          select: {
            id: true,
            name: true,
            email: true,
          },
        },
      },
    });

    // TODO: Notify relevant parties about the update

    res.json({
      status: 'success',
      data: { repair },
    });
  } catch (error) {
    next(error);
  }
});

// Add message to repair request
router.post('/:id/messages', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { content } = z.object({ content: z.string().min(1) }).parse(req.body);

    // Verify user has access to the repair request
    const repair = await prisma.repairRequest.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { requestedById: req.user.id },
          { assignedToId: req.user.id },
          {
            property: {
              OR: [
                { ownerId: req.user.id },
                { tenants: { some: { id: req.user.id } } },
              ],
            },
          },
        ],
      },
    });

    if (!repair) {
      throw new AppError(404, 'Repair request not found or you do not have access to it');
    }

    const message = await prisma.message.create({
      data: {
        content,
        repairRequestId: req.params.id,
        senderType: 'TENANT', // TODO: Determine sender type based on user role
      },
    });

    // TODO: Notify relevant parties about the new message

    res.status(201).json({
      status: 'success',
      data: { message },
    });
  } catch (error) {
    next(error);
  }
});

export const repairRouter = router; 