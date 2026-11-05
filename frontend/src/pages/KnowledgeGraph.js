import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { documentService, knowledgeGraphService } from '../services/api';
import { Search, Filter, Map as MapIcon, BookOpen, Brain, Loader2, Play, ZoomIn, ZoomOut, RefreshCw, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

const KnowledgeGraph = () => {
  const navigate = useNavigate();
  const graphRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState('');
  const [subject, setSubject] = useState('');
  const [topic, setTopic] = useState('');
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [selectedNode, setSelectedNode] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [progress, setProgress] = useState([]);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [dragOrigin, setDragOrigin] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const { data } = await documentService.list();
        setDocuments(data || []);
        if (data?.length) {
          setSelectedDocument(data[0].id);
        }
      } catch (error) {
        toast.error('Failed to load documents');
      }
    };
    loadDocuments();
  }, []);

  const visibleConcepts = useMemo(() => {
    if (!graph?.concepts) return [];
    return graph.concepts.filter((node) => {
      const searchMatch = !search || node.name.toLowerCase().includes(search.toLowerCase()) || node.definition.toLowerCase().includes(search.toLowerCase());
      const filterMatch = filter === 'all' || node.type === filter;
      return searchMatch && filterMatch;
    });
  }, [graph, search, filter]);

  const conceptMap = useMemo(() => {
    return visibleConcepts.map((node, index) => {
      const row = Math.floor(index / 4);
      const column = index % 4;
      return {
        ...node,
        x: 180 + column * 200 + (row % 2) * 25,
        y: 130 + row * 155,
      };
    });
  }, [visibleConcepts]);

  const conceptLookup = useMemo(() => {
    const map = new Map();
    conceptMap.forEach((node) => map.set(node.id, node));
    return map;
  }, [conceptMap]);

  useEffect(() => {
    if (!selectedNode && conceptMap[0]) {
      setSelectedNode(conceptMap[0]);
    }
  }, [conceptMap, selectedNode]);

  const fetchProgress = async (mapId) => {
    if (!mapId) return;
    try {
      const { data } = await knowledgeGraphService.getProgress(mapId);
      setProgress(Array.isArray(data) ? data : []);
    } catch (error) {
      setProgress([]);
    }
  };

  const handleGenerateGraph = async () => {
    if (!selectedDocument) {
      toast.error('Select a document first');
      return;
    }

    setLoading(true);
    try {
      const { data } = await knowledgeGraphService.generate(selectedDocument, subject, topic);
      setGraph(data);
      setSelectedNode((data?.concepts || [])[0] || null);
      setAssessment(null);
      await fetchProgress(data?.id);
      toast.success('Concept map generated');
    } catch (error) {
      toast.error(error?.response?.data?.detail || 'Unable to generate the concept map');
    } finally {
      setLoading(false);
    }
  };

  const handleAssess = async (node) => {
    if (!graph || !node) return;
    try {
      const { data } = await knowledgeGraphService.assess(graph.id, node.id, 'short');
      setAssessment(data);
    } catch (error) {
      toast.error('Unable to generate a quick assessment for this concept');
    }
  };

  const handleSaveProgress = async (status) => {
    if (!graph || !selectedNode) return;
    try {
      const payload = {
        concept_id: selectedNode.id,
        concept_name: selectedNode.name,
        status,
        score: status === 'strong' ? 0.9 : 0.55,
      };
      await knowledgeGraphService.saveProgress(graph.id, payload);
      await fetchProgress(graph.id);
      toast.success(`Marked “${selectedNode.name}” as ${status}`);
    } catch (error) {
      toast.error('Unable to save progress');
    }
  };

  const handleZoom = (delta) => setZoom((current) => clamp(current + delta, 0.7, 1.8));

  const handlePointerDown = (event) => {
    setDragging(true);
    setDragOrigin({ x: event.clientX - pan.x, y: event.clientY - pan.y });
  };

  const handlePointerMove = (event) => {
    if (!dragging) return;
    setPan({
      x: event.clientX - dragOrigin.x,
      y: event.clientY - dragOrigin.y,
    });
  };

  const handlePointerUp = () => setDragging(false);

  const selectedDocumentInfo = documents.find((doc) => doc.id === selectedDocument) || null;

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-8 md:py-10 mt-16 md:mt-0">
        <div className="flex flex-col gap-6">
          <div className="card p-6 md:p-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="rounded-2xl border-2 border-[#0A0A0A] bg-[#CDB4DB] p-3 neo-shadow">
                <MapIcon className="w-8 h-8 text-[#0A0A0A]" strokeWidth={2.5} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70 font-bold">Knowledge graph</p>
                <h1 className="text-3xl md:text-4xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  AI concept map builder
                </h1>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 " data-testid="knowledge-graph-form">
              <div className="md:col-span-2">
                <label className="block text-xs font-black uppercase tracking-[0.18em] text-[#0A0A0A]/75 mb-2">Source document</label>
                <select value={selectedDocument} onChange={(e) => setSelectedDocument(e.target.value)} className="input-field">
                  <option value="">Choose a PDF or source document</option>
                  {documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>{doc.original_filename}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-black uppercase tracking-[0.18em] text-[#0A0A0A]/75 mb-2">Subject</label>
                <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Biology" className="input-field" />
              </div>
              <div>
                <label className="block text-xs font-black uppercase tracking-[0.18em] text-[#0A0A0A]/75 mb-2">Topic</label>
                <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Photosynthesis" className="input-field" />
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <button onClick={handleGenerateGraph} disabled={loading || !selectedDocument} className="btn-primary inline-flex items-center gap-2" data-testid="generate-graph-btn">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />}
                {loading ? 'Generating map...' : 'Generate concept map'}
              </button>
              {graph && (
                <button onClick={() => setGraph(null)} className="btn-secondary inline-flex items-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  Clear
                </button>
              )}
            </div>
          </div>

          {graph ? (
            <>
              <div className="card p-4 md:p-5">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70 font-bold">Current map</p>
                    <h2 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>{graph.title || selectedDocumentInfo?.original_filename || 'Knowledge map'}</h2>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="flex items-center gap-2 rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2">
                      <Search className="w-4 h-4 text-[#0A0A0A]" />
                      <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search concepts" className="bg-transparent outline-none min-w-[160px] text-sm" />
                    </div>
                    <div className="flex items-center gap-2 rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2">
                      <Filter className="w-4 h-4 text-[#0A0A0A]" />
                      <select value={filter} onChange={(e) => setFilter(e.target.value)} className="bg-transparent outline-none text-sm">
                        <option value="all">All</option>
                        <option value="foundation">Foundation</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="core">Core</option>
                      </select>
                    </div>
                    <button onClick={() => handleZoom(0.12)} className="rounded-xl border-2 border-[#0A0A0A] bg-white p-2"><ZoomIn className="w-4 h-4" /></button>
                    <button onClick={() => handleZoom(-0.12)} className="rounded-xl border-2 border-[#0A0A0A] bg-white p-2"><ZoomOut className="w-4 h-4" /></button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-[1.5fr_0.8fr] gap-6">
                <div className="card overflow-hidden">
                  <div
                    ref={graphRef}
                    className="relative h-[640px] w-full overflow-hidden rounded-2xl bg-[radial-gradient(circle_at_top,_rgba(205,180,219,0.35),_transparent_55%)]"
                    onMouseDown={handlePointerDown}
                    onMouseMove={handlePointerMove}
                    onMouseUp={handlePointerUp}
                    onMouseLeave={handlePointerUp}
                  >
                    <svg viewBox="0 0 1100 700" className="h-full w-full">
                      <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
                        {graph.relationships?.map((relationship, index) => {
                          const sourceNode = conceptLookup.get(relationship.source) || conceptLookup.get(relationship.source.toLowerCase());
                          const targetNode = conceptLookup.get(relationship.target) || conceptLookup.get(relationship.target.toLowerCase());
                          if (!sourceNode || !targetNode) return null;
                          return (
                            <g key={`${relationship.source}-${relationship.target}-${index}`}>
                              <path d={`M ${sourceNode.x} ${sourceNode.y} C ${sourceNode.x + 80},${sourceNode.y - 25} ${targetNode.x - 80},${targetNode.y + 25} ${targetNode.x} ${targetNode.y}`} fill="none" stroke={relationship.type === 'depends_on' ? '#FF865E' : '#7DAE7E'} strokeWidth="2" strokeDasharray={relationship.evidence_type === 'inferred' ? '8 6' : '0'} />
                              <circle cx={(sourceNode.x + targetNode.x) / 2} cy={(sourceNode.y + targetNode.y) / 2} r="3" fill="#0A0A0A" />
                            </g>
                          );
                        })}

                        {conceptMap.map((node) => (
                          <g key={node.id} transform={`translate(${node.x} ${node.y})`} onClick={() => setSelectedNode(node)} className="cursor-pointer">
                            <rect
                              width="150"
                              height="70"
                              rx="16"
                              fill={selectedNode?.id === node.id ? '#FFD166' : '#FDFBF7'}
                              stroke="#0A0A0A"
                              strokeWidth="2"
                              className="neo-shadow"
                            />
                            <text x="75" y="30" textAnchor="middle" fontSize="14" fontWeight="700" fill="#0A0A0A">{node.name}</text>
                            <text x="75" y="48" textAnchor="middle" fontSize="11" fill="#0A0A0A">{node.type}</text>
                          </g>
                        ))}
                      </g>
                    </svg>
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="card p-5">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70 font-bold">Selected concept</p>
                        <h3 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>{selectedNode?.name || 'No concept selected'}</h3>
                      </div>
                      {selectedNode && (
                        <button onClick={() => handleAssess(selectedNode)} className="btn-secondary inline-flex items-center gap-2">
                          <Brain className="w-4 h-4" />
                          Assess
                        </button>
                      )}
                    </div>

                    {selectedNode ? (
                      <div className="mt-5 space-y-4 text-sm text-[#0A0A0A]">
                        <p><span className="font-black uppercase tracking-[0.14em] text-[#0A0A0A]/70">Definition</span><br />{selectedNode.definition}</p>
                        <div>
                          <p className="font-black uppercase tracking-[0.14em] text-[#0A0A0A]/70">Prerequisites</p>
                          <ul className="list-disc ml-5 mt-2 space-y-1">
                            {(selectedNode.prerequisites?.length ? selectedNode.prerequisites : ['Not specified']).map((item) => <li key={item}>{item}</li>)}
                          </ul>
                        </div>
                        <div>
                          <p className="font-black uppercase tracking-[0.14em] text-[#0A0A0A]/70">Examples</p>
                          <ul className="list-disc ml-5 mt-2 space-y-1">
                            {(selectedNode.examples?.length ? selectedNode.examples : ['No explicit examples in the current source']).map((item) => <li key={item}>{item}</li>)}
                          </ul>
                        </div>
                        <div>
                          <p className="font-black uppercase tracking-[0.14em] text-[#0A0A0A]/70">Related topics</p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {(selectedNode.related_topics?.length ? selectedNode.related_topics : ['General topic']).map((item) => (
                              <span key={item} className="rounded-full border-2 border-[#0A0A0A] bg-[#CDB4DB] px-2 py-1 text-xs font-semibold">{item}</span>
                            ))}
                          </div>
                        </div>
                        <div className="flex gap-2 flex-wrap pt-2">
                          <button onClick={() => handleSaveProgress('weak')} className="btn-secondary">Mark as weak</button>
                          <button onClick={() => handleSaveProgress('strong')} className="btn-secondary">Mark as strong</button>
                          <button onClick={() => navigate(`/tutor?doc=${selectedDocument}&question=${encodeURIComponent(selectedNode.name)}`)} className="btn-primary inline-flex items-center gap-2"><Play className="w-4 h-4" /> Start revision</button>
                        </div>
                      </div>
                    ) : (
                      <p className="mt-4 text-sm text-[#0A0A0A]/70">Select a concept node to view the explanation.</p>
                    )}
                  </div>

                  <div className="card p-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70 font-bold">Quick assessment</p>
                    {assessment ? (
                      <div className="mt-4 space-y-3 text-sm text-[#0A0A0A]">
                        <p className="font-black text-base">{assessment.prompt}</p>
                        {assessment.options && (
                          <ul className="list-disc ml-5 space-y-1">
                            {assessment.options.map((option) => <li key={option}>{option}</li>)}
                          </ul>
                        )}
                        <p><span className="font-bold">Difficulty:</span> {assessment.difficulty}</p>
                        <p className="text-[#0A0A0A]/80"><span className="font-bold">Hint:</span> {assessment.explanation}</p>
                      </div>
                    ) : (
                      <p className="mt-3 text-sm text-[#0A0A0A]/70">Choose a concept and generate a short assessment to test understanding.</p>
                    )}
                  </div>

                  <div className="card p-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-[#0A0A0A]/70 font-bold">Progress</p>
                    <div className="mt-4 space-y-2">
                      {progress.length ? progress.map((entry) => (
                        <div key={`${entry.concept_id}-${entry.updated_at}`} className="flex items-center justify-between rounded-xl border-2 border-[#0A0A0A] bg-white px-3 py-2">
                          <span className="text-sm font-semibold text-[#0A0A0A]">{entry.concept_name || entry.concept_id}</span>
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#CDB4DB] px-2 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-[#0A0A0A]">
                            <CheckCircle2 className="w-3 h-3" />{entry.status}
                          </span>
                        </div>
                      )) : <p className="text-sm text-[#0A0A0A]/70">No concept progress saved yet.</p>}
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="card p-10 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-[#0A0A0A] bg-[#FFD166] neo-shadow">
                <MapIcon className="w-8 h-8 text-[#0A0A0A]" strokeWidth={2.5} />
              </div>
              <h3 className="text-2xl font-black text-[#0A0A0A]" style={{ fontFamily: 'Outfit, sans-serif' }}>No concept map yet</h3>
              <p className="mt-3 text-[#0A0A0A]/75">Select a document and generate a map to reveal key concepts, dependencies, and revision prompts.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph;
