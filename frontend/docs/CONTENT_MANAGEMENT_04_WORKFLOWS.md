# Content Management Part 4: Content Workflows

> Editorial workflows, approvals, scheduling, and version management

**Series:** Content Management
**Previous:** [Part 3: Content Delivery](./CONTENT_MANAGEMENT_03_DELIVERY.md)

---

## Table of Contents

1. [Editorial Workflow](#editorial-workflow)
2. [Role-Based Permissions](#role-based-permissions)
3. [Content Scheduling](#content-scheduling)
4. [Version History](#version-history)
5. [Content Preview](#content-preview)
6. [Bulk Operations](#bulk-operations)

---

## Editorial Workflow

### Workflow States

```typescript
// Content workflow states

interface WorkflowStates {
  draft: {
    description: 'Content in progress, not visible publicly';
    permissions: 'Editors and above can view and edit';
    actions: ['edit', 'delete', 'submit for review'];
  };

  inReview: {
    description: 'Pending approval, not visible publicly';
    permissions: 'Reviewers and above can view and approve';
    actions: ['approve', 'request changes', 'reject'];
  };

  scheduled: {
    description: 'Approved and scheduled for future publish';
    permissions: 'Read-only for editors';
    actions: ['unschedule', 'edit draft'];
  };

  published: {
    description: 'Live and visible publicly';
    permissions: 'Read-only for editors';
    actions: ['unpublish', 'create new version'];
  };

  archived: {
    description: 'No longer visible, preserved for reference';
    permissions: 'Admins only';
    actions: ['restore', 'permanently delete'];
  };
}
```

### Sanity Workflow Implementation

```typescript
// Sanity document status tracking

export const documentWithWorkflow = defineType({
  name: 'destination',
  title: 'Destination',
  type: 'document',
  fields: [
    // ... existing fields

    // Workflow status
    defineField({
      name: 'workflowStatus',
      title: 'Workflow Status',
      type: 'string',
      initialValue: 'draft',
      options: {
        list: [
          { title: '📝 Draft', value: 'draft' },
          { title: '👀 In Review', value: 'inReview' },
          { title: '📅 Scheduled', value: 'scheduled' },
          { title: '✅ Published', value: 'published' },
          { title: '📦 Archived', value: 'archived' },
        ],
      },
      validation: (Rule) => Rule.required(),
    }),

    // Published date
    defineField({
      name: 'publishedAt',
      title: 'Published At',
      type: 'datetime',
      readOnly: true,
    }),

    // Scheduled publish date
    defineField({
      name: 'publishAt',
      title: 'Schedule Publish',
      type: 'datetime',
      hidden: ({ parent }) =>
        !['inReview', 'scheduled'].includes(parent.workflowStatus),
    }),

    // Author
    defineField({
      name: 'author',
      title: 'Author',
      type: 'string',
      initialValue: () => {
        // Set from authenticated user
        const userId = getSanityUserId();
        return userId;
      },
      readOnly: true,
    }),

    // Last edited by
    defineField({
      name: 'lastEditedBy',
      title: 'Last Edited By',
      type: 'string',
      readOnly: true,
    }),

    // Reviewer
    defineField({
      name: 'reviewer',
      title: 'Reviewer',
      type: 'string',
      hidden: ({ parent }) =>
        !['inReview', 'scheduled', 'published'].includes(parent.workflowStatus),
    }),

    // Rejection reason
    defineField({
      name: 'rejectionReason',
      title: 'Rejection Reason',
      type: 'text',
      hidden: ({ parent }) => parent.workflowStatus !== 'draft',
    }),
  ],

  // Filter documents by status in studio
  preview: {
    select: {
      title: 'title',
      status: 'workflowStatus',
      media: 'heroImage',
    },
    prepare(selection) {
      const { title, status } = selection;
      const statusEmoji = {
        draft: '📝',
        inReview: '👀',
        scheduled: '📅',
        published: '✅',
        archived: '📦',
      };
      return {
        title,
        subtitle: `${statusEmoji[status as keyof typeof statusEmoji]} ${status}`,
      };
    },
  },
});
```

### Workflow Actions

```typescript
// Workflow action handlers

import { writeClient } from '@/lib/sanity/client';

// Submit for review
export async function submitForReview(documentId: string) {
  return writeClient
    .patch(documentId)
    .set({
      workflowStatus: 'inReview',
      submittedAt: new Date().toISOString(),
    })
    .commit();
}

// Approve content
export async function approveContent(
  documentId: string,
  reviewerId: string
) {
  return writeClient
    .patch(documentId)
    .set({
      workflowStatus: 'published',
      reviewer,
      publishedAt: new Date().toISOString(),
      lastEditedBy: reviewerId,
    })
    .commit();
}

// Request changes
export async function requestChanges(
  documentId: string,
  reason: string
) {
  return writeClient
    .patch(documentId)
    .set({
      workflowStatus: 'draft',
      rejectionReason: reason,
    })
    .commit();
}

// Schedule publish
export async function schedulePublish(
  documentId: string,
  publishAt: Date
) {
  return writeClient
    .patch(documentId)
    .set({
      workflowStatus: 'scheduled',
      publishAt: publishAt.toISOString(),
    })
    .commit();
}

// Unpublish
export async function unpublishContent(documentId: string) {
  return writeClient
    .patch(documentId)
    .set({
      workflowStatus: 'draft',
      publishedAt: null,
    })
    .commit();
}

// Archive
export async function archiveContent(documentId: string) {
  return writeClient
    .patch(documentId)
    .set({
      workflowStatus: 'archived',
      archivedAt: new Date().toISOString(),
    })
    .commit();
}
```

---

## Role-Based Permissions

### Permission Model

```typescript
// Content management roles

interface ContentRoles {
  admin: {
    permissions: [
      'create',
      'edit',
      'delete',
      'publish',
      'unpublish',
      'archive',
      'restore',
      'manage users',
      'manage settings',
    ];
    scope: 'All content';
  };

  publisher: {
    permissions: ['create', 'edit', 'publish', 'unpublish', 'schedule'];
    scope: 'Assigned content types';
  };

  editor: {
    permissions: ['create', 'edit', 'submit for review'];
    scope: 'Assigned content types';
  };

  reviewer: {
    permissions: ['view drafts', 'approve', 'request changes'];
    scope: 'Assigned for review';
  };

  contributor: {
    permissions: ['create own', 'edit own'];
    scope: 'Own content only';
  };
}
```

### Sanity Actions Implementation

```typescript
// Sanity Actions for workflow

// sanity/actions/publish.ts
import { defineAction } from 'sanity';
import { approveContent } from '@/lib/workflows';

export const publishAction = defineAction({
  name: 'publish',
  title: 'Publish',
  description: 'Publish this document',
  on: 'document',
  input: {
    type: 'object',
    properties: {
      skipReview: {
        type: 'boolean',
        description: 'Skip review and publish immediately',
      },
    },
  },
  execute: async ({ id, getClient, schema }) => {
    const client = getClient({ apiVersion: '2025-01-01' });
    const userId = await getCurrentUserId();

    await approveContent(id, userId);

    return {
      message: 'Document published successfully',
    };
  },
});

// sanity/actions/requestReview.ts
export const requestReviewAction = defineAction({
  name: 'requestReview',
  title: 'Submit for Review',
  description: 'Submit this document for editorial review',
  on: 'document',
  execute: async ({ id, getClient }) => {
    const client = getClient({ apiVersion: '2025-01-01' });

    await submitForReview(id);

    // Notify reviewers
    await notifyReviewers(id);

    return {
      message: 'Document submitted for review',
    };
  },
});
```

---

## Content Scheduling

### Scheduled Publishing

```typescript
// Scheduled content publishing

import { cron } from '@vercel/triggers-job';
import { writeClient } from '@/lib/sanity/client';
import { revalidateTag } from 'next/cache';

// Find scheduled content ready to publish
async function findScheduledContent() {
  return writeClient.fetch(
    groq`*[
      workflowStatus == "scheduled" &&
      publishAt <= $now
    ].{_id, _type, slug}`,
    { now: new Date().toISOString() }
  );
}

// Publish scheduled content
async function publishScheduledContent() {
  const scheduled = await findScheduledContent();

  for (const doc of scheduled) {
    await writeClient
      .patch(doc._id)
      .set({
        workflowStatus: 'published',
        publishedAt: new Date().toISOString(),
      })
      .commit();

    // Revalidate cache
    revalidateTag(doc._type);
    revalidateTag(`${doc._type}-${doc.slug.current}`);

    console.log(`Published scheduled ${doc._type}: ${doc.slug.current}`);
  }

  return { published: scheduled.length };
}

// Vercel Cron job
export const config = {
  schedule: '*/5 * * * *', // Every 5 minutes
};

export default cron.handler(async (req, res) => {
  const result = await publishScheduledContent();

  return res.status(200).json(result);
});
```

### Content Expiration

```typescript
// Auto-unpublish expired content

export const documentWithExpiration = defineType({
  name: 'deal',
  title: 'Deal',
  type: 'document',
  fields: [
    // ... existing fields

    defineField({
      name: 'expiresAt',
      title: 'Expires At',
      type: 'datetime',
      description: 'Automatically unpublish after this date',
    }),

    defineField({
      name: 'expired',
      title: 'Expired',
      type: 'boolean',
      initialValue: false,
      readOnly: true,
    }),
  ],
});

// Cron job to expire content
async function expireContent() {
  const expired = await writeClient.fetch(
    groq`*[
      workflowStatus == "published" &&
      expiresAt <= $now &&
      expired == false
    ].{_id, _type, slug}`,
    { now: new Date().toISOString() }
  );

  for (const doc of expired) {
    await writeClient
      .patch(doc._id)
      .set({
        expired: true,
        workflowStatus: 'archived',
        expiredAt: new Date().toISOString(),
      })
      .commit();

    revalidateTag(doc._type);
    revalidateTag(`${doc._type}-${doc.slug.current}`);

    console.log(`Expired ${doc._type}: ${doc.slug.current}`);
  }

  return { expired: expired.length };
}
```

---

## Version History

### Document Versions

```typescript
// Version tracking with Sanity

// Enable history in dataset
// sanity dataset create production --default --public

// Query document history
async function getDocumentHistory(documentId: string) {
  return writeClient.fetch({
    uri: `/projects/${projectId}/datasets/${dataset}/documents/${documentId}/history`,
    method: 'GET',
  });
}

// Restore previous version
async function restoreVersion(
  documentId: string,
  versionId: string
) {
  return writeClient.fetch({
    uri: `/projects/${projectId}/datasets/${dataset}/documents/${documentId}/history/${versionId}/restore`,
    method: 'POST',
  });
}
```

### Change Tracking

```typescript
// Audit log for content changes

export const contentAudit = defineType({
  name: 'contentAudit',
  title: 'Content Audit Log',
  type: 'document',
  fields: [
    defineField({
      name: 'documentId',
      title: 'Document ID',
      type: 'string',
    }),
    defineField({
      name: 'documentType',
      title: 'Document Type',
      type: 'string',
    }),
    defineField({
      name: 'action',
      title: 'Action',
      type: 'string',
      options: {
        list: [
          'created',
          'updated',
          'published',
          'unpublished',
          'deleted',
          'restored',
        ],
      },
    }),
    defineField({
      name: 'userId',
      title: 'User',
      type: 'string',
    }),
    defineField({
      name: 'timestamp',
      title: 'Timestamp',
      type: 'datetime',
      initialValue: () => new Date().toISOString(),
    }),
    defineField({
      name: 'changes',
      title: 'Changes',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'object',
          fields: [
            defineField({ name: 'field', type: 'string' }),
            defineField({ name: 'oldValue', type: 'string' }),
            defineField({ name: 'newValue', type: 'string' }),
          ],
        }),
      ],
    }),
  ],
});

// Create audit entry on changes
async function logChange(
  documentId: string,
  action: string,
  changes: unknown[],
  userId: string
) {
  return writeClient.create({
    _type: 'contentAudit',
    documentId,
    documentType: documentId.split('-')[0],
    action,
    userId,
    changes,
    timestamp: new Date().toISOString(),
  });
}
```

---

## Content Preview

### Live Preview

```typescript
// Sanity Studio preview configuration

// sanity.config.ts
import { defineConfig } from 'sanity';
import { previewUrl } from '@/sanity/plugins/previewUrl';

export default defineConfig({
  // ... config
  plugins: [
    previewUrl({
      previewUrl: {
        draftMode: {
          enable: '/api/draft',
        },
      },
    }),
  ],
});

// Draft mode API route
import { draftMode } from 'next/headers';
import { redirect } from 'next/navigation';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const secret = searchParams.get('secret');
  const slug = searchParams.get('slug');
  const type = searchParams.get('type');

  if (secret !== process.env.SANITY_PREVIEW_SECRET) {
    return new Response('Invalid secret', { status: 401 });
  }

  const draft = await draftMode();
  draft.enable();

  redirect(`/${type}/${slug}`);
}
```

### Preview Component

```typescript
// Live preview in studio

import { IframePreview } from 'sanity-plugin-iframe-preview';

// Add to desk structure
export const defaultDocumentNode = (S, { schemaType }) => {
  switch (schemaType) {
    case 'destination':
      return S.document().views([
        S.view.form(),
        S.view
          .component(IframePreview)
          .title('Live Preview')
          .options({
            url: (doc) =>
              `/api/preview?slug=${doc.slug.current}&type=destination`,
            reload: {
              button: true,
            },
          }),
      ]);
    default:
      return S.document().views([S.view.form()]);
  }
};
```

---

## Bulk Operations

### Bulk Import

```typescript
// Bulk content import

import { createClient } from '@sanity/client';
import { readFileSync } from 'fs';
import { chunk } from 'lodash';

const client = createClient({
  projectId: process.env.SANITY_PROJECT_ID!,
  dataset: process.env.SANITY_DATASET!,
  token: process.env.SANITY_WRITE_TOKEN!,
});

export async function bulkImport(
  data: unknown[],
  typeName: string
) {
  const BATCH_SIZE = 100;
  const batches = chunk(data, BATCH_SIZE);

  let imported = 0;
  let errors = 0;

  for (const [index, batch] of batches.entries()) {
    try {
      const transaction = batch.reduce((tx, item) => {
        return tx.create({
          _type: typeName,
          ...item,
        });
      }, client.transaction());

      await transaction.commit();
      imported += batch.length;

      console.log(`Imported batch ${index + 1}/${batches.length}`);
    } catch (error) {
      console.error(`Batch ${index + 1} failed:`, error);
      errors++;

      // Try individual imports
      for (const item of batch) {
        try {
          await client.create({
            _type: typeName,
            ...item,
          });
          imported++;
        } catch (itemError) {
          console.error('Item import failed:', itemError);
          errors++;
        }
      }
    }
  }

  return { imported, errors };
}
```

### Bulk Export

```typescript
// Bulk content export

import { createClient } from '@sanity/client';
import { writeFileSync } from 'fs';

const client = createClient({
  projectId: process.env.SANITY_PROJECT_ID!,
  dataset: process.env.SANITY_DATASET!,
  token: process.env.SANITY_WRITE_TOKEN!,
});

export async function bulkExport(typeName: string, filename: string) {
  const documents = await client.fetch(
    groq`*[_type == $typeName]`,
    { typeName }
  );

  writeFileSync(filename, JSON.stringify(documents, null, 2));

  console.log(`Exported ${documents.length} documents to ${filename}`);

  return documents.length;
}

// Export all content
export async function exportAllContent(outputDir: string) {
  const types = ['destination', 'accommodation', 'deal', 'blogPost'];

  for (const type of types) {
    const filename = `${outputDir}/${type}.json`;
    await bulkExport(type, filename);
  }
}
```

### Bulk Operations

```typescript
// Bulk updates and deletes

export async function bulkUpdate(
  typeName: string,
  updates: Record<string, unknown>
) {
  const documents = await client.fetch(
    groq`*[_type == $typeName]._id`,
    { typeName }
  );

  const BATCH_SIZE = 100;
  const batches = chunk(documents, BATCH_SIZE);

  for (const batch of batches) {
    const transaction = batch.reduce((tx, id) => {
      return tx.patch(id, { set: updates });
    }, client.transaction());

    await transaction.commit();
  }

  return documents.length;
}

export async function bulkDelete(
  typeName: string,
  filter: Record<string, unknown>
) {
  const documents = await client.fetch(
    groq`*[_type == $typeName && filter == $filter]._id`,
    { typeName, filter }
  );

  const BATCH_SIZE = 100;
  const batches = chunk(documents, BATCH_SIZE);

  for (const batch of batches) {
    const transaction = batch.reduce((tx, id) => {
      return tx.delete(id);
    }, client.transaction());

    await transaction.commit();
  }

  return documents.length;
}
```

---

## Summary

Content workflows for the travel agency platform:

- **Editorial Workflow**: Draft → Review → Scheduled → Published → Archived
- **Permissions**: Role-based access (Admin, Publisher, Editor, Reviewer, Contributor)
- **Scheduling**: Cron jobs for publish/unpublish/expire
- **Version History**: Document history tracking and restore
- **Preview**: Live preview in studio with draft mode
- **Bulk Ops**: Import/export, batch updates

**Key Workflow Decisions:**
- Workflow status field on all documents
- Sanity Actions for workflow transitions
- Cron jobs for scheduled operations
- Audit log for change tracking
- Live preview for editors

---

**Series Complete:** [Content Management Master Index](./CONTENT_MANAGEMENT_MASTER_INDEX.md)
