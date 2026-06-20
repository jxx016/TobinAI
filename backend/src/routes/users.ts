import { Router, Request, Response, NextFunction } from 'express';
import { prisma } from '../index';
import { AppError } from '../middleware/errorHandler';
import { requireAuth } from '../middleware/auth';

const router = Router();
router.use(requireAuth);

// Get current user profile
router.get('/me', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.id },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        phoneNumber: true,
      },
    });
    if (!user) throw new AppError(404, 'User not found');
    res.json({ status: 'success', data: { user } });
  } catch (error) {
    next(error);
  }
});

export const userRouter = router; 