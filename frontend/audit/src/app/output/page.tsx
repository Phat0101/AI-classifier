'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  ChevronRight, 
  ChevronDown, 
  Folder, 
  File, 
  Download, 
  Trash2,
  Home,
  RefreshCw,
  Calendar,
  HardDrive
} from 'lucide-react';

interface FileItem {
  name: string;
  path: string;
  size: number;
  type: 'file' | 'directory';
  modified: number;
}

interface Run {
  name: string;
  path: string;
  modified: number;
  size: number;
}

interface ExpandedDirectories {
  [key: string]: FileItem[] | null | 'collapsed'; // null means loading, 'collapsed' means not expanded
}

export default function OutputPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [expandedDirs, setExpandedDirs] = useState<ExpandedDirectories>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const fetchRuns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/output/runs`);
      if (!response.ok) throw new Error('Failed to fetch runs');
      const data = await response.json();
      setRuns(data.runs || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load runs');
    } finally {
      setLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  const loadDirectory = async (path: string) => {
    // Set loading state
    setExpandedDirs(prev => ({ ...prev, [path]: null }));
    
    try {
      const response = await fetch(`${API_URL}/api/output/browse?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to load directory');
      const data = await response.json();
      
      setExpandedDirs(prev => ({ ...prev, [path]: data.items }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load directory');
      setExpandedDirs(prev => ({ ...prev, [path]: 'collapsed' }));
    }
  };

  const toggleDirectory = (path: string) => {
    const currentState = expandedDirs[path];
    
    if (!currentState || currentState === 'collapsed') {
      // Not loaded yet or collapsed, load it
      loadDirectory(path);
    } else {
      // Already loaded or loading, collapse it
      setExpandedDirs(prev => {
        const newState = { ...prev };
        newState[path] = 'collapsed';
        // Also collapse all subdirectories
        Object.keys(newState).forEach(key => {
          if (key.startsWith(path + '/')) {
            newState[key] = 'collapsed';
          }
        });
        return newState;
      });
    }
  };

  const downloadFile = async (path: string, filename: string) => {
    try {
      const response = await fetch(`${API_URL}/api/output/download?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to download file');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download file');
    }
  };

  const deleteItem = async (path: string) => {
    if (!confirm(`Are you sure you want to delete ${path}?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/output/delete?path=${encodeURIComponent(path)}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete item');
      
      // Refresh the runs list
      await fetchRuns();
      // Clear expanded directories to force reload
      setExpandedDirs({});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete item');
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const renderFileItem = (item: FileItem, depth: number = 0) => {
    const dirState = expandedDirs[item.path];
    const isExpanded = dirState && dirState !== 'collapsed';
    const isLoading = dirState === null;
    const isDirectory = item.type === 'directory';
    
    return (
      <div key={item.path}>
        <div 
          className={`
            flex items-center justify-between p-2 hover:bg-muted/50 rounded-md group
            ${depth > 0 ? 'ml-' + (depth * 4) : ''}
          `}
          style={{ marginLeft: `${depth * 1.5}rem` }}
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {isDirectory ? (
              <button
                onClick={() => toggleDirectory(item.path)}
                className="flex items-center gap-2 flex-1 min-w-0 text-left hover:underline"
              >
                {isLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
                ) : isExpanded ? (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                )}
                <Folder className="h-4 w-4 text-blue-500 flex-shrink-0" />
                <span className="text-sm font-medium truncate">{item.name}</span>
              </button>
            ) : (
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <File className="h-4 w-4 text-muted-foreground flex-shrink-0 ml-6" />
                <span className="text-sm truncate">{item.name}</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {!isDirectory && (
              <>
                <span className="text-xs text-muted-foreground">
                  {formatBytes(item.size)}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 opacity-0 group-hover:opacity-100"
                  onClick={() => downloadFile(item.path, item.name)}
                >
                  <Download className="h-3 w-3" />
                </Button>
              </>
            )}
            {isDirectory && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive"
                onClick={() => deleteItem(item.path)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
        
        {/* Render subdirectory contents */}
        {isDirectory && isExpanded && !isLoading && expandedDirs[item.path] && (
          <div>
            {(expandedDirs[item.path] as FileItem[]).map(subItem => 
              renderFileItem(subItem, depth + 1)
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight">
                Output Browser
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Browse and download audit results
              </p>
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline"
                onClick={fetchRuns}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button 
                variant="default"
                onClick={() => window.location.href = '/'}
              >
                <Home className="h-4 w-4 mr-2" />
                Home
              </Button>
            </div>
          </div>
        </header>

        {error && (
          <Card className="border-destructive mb-4">
            <CardContent className="pt-6">
              <p className="text-sm text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {loading && runs.length === 0 ? (
          <Card>
            <CardContent className="pt-6 flex items-center justify-center py-12">
              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
            </CardContent>
          </Card>
        ) : runs.length === 0 ? (
          <Card>
            <CardContent className="pt-6 text-center py-12">
              <HardDrive className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground">
                No output directories found. Process some files to see results here.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {runs.map((run) => (
              <Card key={run.path}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        {run.name}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        Modified: {formatDate(run.modified)} · Size: {formatBytes(run.size)}
                      </CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => deleteItem(run.path)}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Run
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="border rounded-lg p-2">
                    {renderFileItem({
                      name: run.name,
                      path: run.path,
                      size: run.size,
                      type: 'directory',
                      modified: run.modified
                    }, 0)}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

