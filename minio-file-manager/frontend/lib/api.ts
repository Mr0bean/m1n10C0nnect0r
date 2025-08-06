import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9011/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Bucket {
  name: string
  creation_date: string | null
}

export interface MinioObject {
  name: string
  size: number
  etag: string
  last_modified: string | null
  is_dir: boolean
}

export interface ObjectInfo {
  name: string
  size: number
  etag: string
  content_type: string
  last_modified: string | null
  metadata: Record<string, string> | null
}

export interface UploadResponse {
  bucket: string
  object_name: string
  etag: string
  version_id: string | null
}

export interface PresignedUrlResponse {
  url: string
  expires_in: number
}

export const bucketApi = {
  list: async (): Promise<Bucket[]> => {
    const { data } = await api.get('/buckets')
    return data
  },

  create: async (bucketName: string) => {
    const { data } = await api.post('/buckets', { bucket_name: bucketName })
    return data
  },

  delete: async (bucketName: string) => {
    const { data } = await api.delete(`/buckets/${bucketName}`)
    return data
  },

  getPolicy: async (bucketName: string) => {
    const { data } = await api.get(`/buckets/${bucketName}/policy`)
    return data
  },

  setPolicy: async (bucketName: string, policy: any) => {
    const { data } = await api.put(`/buckets/${bucketName}/policy`, { policy })
    return data
  },
}

export const objectApi = {
  list: async (bucketName: string, prefix: string = '', recursive: boolean = true): Promise<MinioObject[]> => {
    const { data } = await api.get(`/objects/${bucketName}`, {
      params: { prefix, recursive }
    })
    return data
  },

  upload: async (bucketName: string, file: File, objectName?: string, metadata?: Record<string, string>) => {
    const formData = new FormData()
    formData.append('file', file)
    if (objectName) formData.append('object_name', objectName)
    if (metadata) formData.append('metadata', JSON.stringify(metadata))

    const { data } = await api.post(`/objects/${bucketName}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return data as UploadResponse
  },

  download: async (bucketName: string, objectName: string) => {
    const response = await api.get(`/objects/${bucketName}/${objectName}/download`, {
      responseType: 'blob',
    })
    return response
  },

  getInfo: async (bucketName: string, objectName: string): Promise<ObjectInfo> => {
    const { data } = await api.get(`/objects/${bucketName}/${objectName}/info`)
    return data
  },

  delete: async (bucketName: string, objectName: string) => {
    const { data } = await api.delete(`/objects/${bucketName}/${objectName}`)
    return data
  },

  copy: async (sourceBucket: string, sourceObject: string, destBucket: string, destObject: string) => {
    const { data } = await api.post('/objects/copy', {
      source_bucket: sourceBucket,
      source_object: sourceObject,
      dest_bucket: destBucket,
      dest_object: destObject,
    })
    return data
  },

  getPresignedUrl: async (bucketName: string, objectName: string, expires: number = 3600, method: 'GET' | 'PUT' = 'GET'): Promise<PresignedUrlResponse> => {
    const { data } = await api.post('/objects/presigned-url', {
      bucket_name: bucketName,
      object_name: objectName,
      expires,
      method,
    })
    return data
  },
}