/**
 * PermissionGate - Conditionally render UI elements based on permissions
 * 
 * Usage examples:
 * 
 * 1. Simple permission check:
 * <PermissionGate feature="apartments" action="create">
 *   <Button>Add Apartment</Button>
 * </PermissionGate>
 * 
 * 2. With fallback:
 * <PermissionGate feature="payments" action="void" fallback={<span>No access</span>}>
 *   <Button variant="destructive">Void Payment</Button>
 * </PermissionGate>
 * 
 * 3. Multiple actions (any):
 * <PermissionGate feature="apartments" actions={['edit', 'delete']}>
 *   <ActionsMenu />
 * </PermissionGate>
 * 
 * 4. Using hooks directly:
 * const canCreate = useCanCreate('apartments');
 * const canEdit = useCanEdit('apartments');
 */

import React, { ReactNode } from 'react';
import { usePermissions } from '../context/AuthContext';
import type { UIPermissions } from '../types';

// =============================================================================
// Types
// =============================================================================

type Feature = keyof UIPermissions;
type Action = 'view' | 'create' | 'edit' | 'delete' | 'void' | 'generate_monthly' | 'export' | 'manage';

interface PermissionGateProps {
  /** Feature area to check (apartments, payments, obligations, etc.) */
  feature: Feature;
  /** Single action to check */
  action?: Action;
  /** Multiple actions - renders if ANY of them are allowed */
  actions?: Action[];
  /** Content to render if permission is granted */
  children: ReactNode;
  /** Optional fallback to render if permission is denied */
  fallback?: ReactNode;
}

// =============================================================================
// Permission Check Helper
// =============================================================================

function hasPermission(
  permissions: UIPermissions,
  feature: Feature,
  action: Action
): boolean {
  const featurePerms = permissions[feature];
  if (!featurePerms) return false;
  
  // Type-safe check for the action using object property access
  const permsObj = featurePerms as unknown as Record<string, boolean>;
  if (action in permsObj) {
    return permsObj[action] ?? false;
  }
  
  return false;
}

// =============================================================================
// PermissionGate Component
// =============================================================================

export const PermissionGate: React.FC<PermissionGateProps> = ({
  feature,
  action,
  actions,
  children,
  fallback = null,
}) => {
  const permissions = usePermissions();
  
  // Determine which actions to check
  const actionsToCheck = actions || (action ? [action] : []);
  
  if (actionsToCheck.length === 0) {
    console.warn('PermissionGate: No action or actions specified');
    return <>{fallback}</>;
  }
  
  // Check if ANY of the specified actions are allowed
  const isAllowed = actionsToCheck.some((a) => hasPermission(permissions, feature, a));
  
  return <>{isAllowed ? children : fallback}</>;
};

// =============================================================================
// useHasPermission Hook - for programmatic checks
// =============================================================================

export function useHasPermission(feature: Feature, action: Action): boolean {
  const permissions = usePermissions();
  return hasPermission(permissions, feature, action);
}

// =============================================================================
// useHasAnyPermission Hook - check multiple actions
// =============================================================================

export function useHasAnyPermission(feature: Feature, actions: Action[]): boolean {
  const permissions = usePermissions();
  return actions.some((action) => hasPermission(permissions, feature, action));
}

// =============================================================================
// useHasAllPermissions Hook - check all actions required
// =============================================================================

export function useHasAllPermissions(feature: Feature, actions: Action[]): boolean {
  const permissions = usePermissions();
  return actions.every((action) => hasPermission(permissions, feature, action));
}

export default PermissionGate;
