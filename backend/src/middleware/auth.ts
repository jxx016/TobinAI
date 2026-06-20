import { Request, Response, NextFunction } from 'express';
import { supabase } from '../index';
import { AppError } from './errorHandler';

export const requireAuth = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  try {
    // Get the session from the Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      throw new AppError(401, 'No token provided');
    }

    const token = authHeader.split(' ')[1];

    // Verify the session with Supabase
    const { data: { user }, error } = await supabase.auth.getUser(token);

    if (error || !user) {
      throw new AppError(401, 'Invalid or expired token');
    }

    // Add user to request object
    req.user = user;
    next();
  } catch (error) {
    next(error);
  }
};

// Extend Express Request type to include user
declare global {
  namespace Express {
    interface Request {
      user?: any; // Replace 'any' with your user type
    }
  }
} 