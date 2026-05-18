import {
  Injectable,
  Logger,
  BadGatewayException,
  ServiceUnavailableException,
  BadRequestException,
} from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { AxiosError } from 'axios';
import {
  NewsSearchDto,
  SummaryGenerateDto,
  ScriptGenerateDto,
  ThumbnailPromptDto,
  SaveResultDto,
  LibraryQueryDto,
} from './content.dto';

@Injectable()
export class ContentService {
  private readonly logger = new Logger(ContentService.name);

  constructor(
    private readonly http: HttpService,
    private readonly config: ConfigService,
  ) {}

  private get backendUrl(): string {
    return this.config.get<string>('backendUrl')!;
  }

  /** Step 1: 주제 기반 뉴스 검색 */
  async searchNews(dto: NewsSearchDto) {
    this.logger.log(`뉴스 검색 — topic=${dto.topic}`);
    try {
      const { data } = await firstValueFrom(
        this.http.post(`${this.backendUrl}/api/v1/news/search`, dto),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, '뉴스 검색');
    }
  }

  /** Step 2-A: 뉴스 요약본 생성 */
  async generateSummary(dto: SummaryGenerateDto) {
    this.logger.log(`요약본 생성 — news_id=${dto.news_id}, language=${dto.language}`);
    try {
      const { data } = await firstValueFrom(
        this.http.post(`${this.backendUrl}/api/v1/news/summary`, dto),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, '요약본 생성');
    }
  }

  /** Step 2-B: 뉴스 스크립트 생성 */
  async generateScript(dto: ScriptGenerateDto) {
    this.logger.log(
      `스크립트 생성 — news_id=${dto.news_id}, duration=${dto.duration}`,
    );
    try {
      const { data } = await firstValueFrom(
        this.http.post(`${this.backendUrl}/api/v1/news/script`, dto),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, '스크립트 생성');
    }
  }

  /** Step 3: 썸네일 프롬프트 생성 */
  async generateThumbnail(dto: ThumbnailPromptDto) {
    this.logger.log(`썸네일 프롬프트 생성 — news_id=${dto.news_id}`);
    try {
      const { data } = await firstValueFrom(
        this.http.post(`${this.backendUrl}/api/v1/news/thumbnail`, dto),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, '썸네일 프롬프트 생성');
    }
  }

  /** Step 4: 결과 저장 */
  async saveResult(dto: SaveResultDto) {
    this.logger.log(`결과 저장 — topic=${dto.topic}`);
    try {
      const { data } = await firstValueFrom(
        this.http.post(`${this.backendUrl}/api/v1/news/save`, dto),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, '결과 저장');
    }
  }

  /** Step 5: 라이브러리 조회 */
  async getLibrary(query: LibraryQueryDto) {
    const params: Record<string, unknown> = {};
    if (query.hashtag) params['hashtag'] = query.hashtag;
    if (query.limit) params['limit'] = query.limit;

    this.logger.log(`라이브러리 조회 — hashtag=${query.hashtag}, limit=${query.limit}`);
    try {
      const { data } = await firstValueFrom(
        this.http.get(`${this.backendUrl}/api/v1/news/library`, { params }),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, '라이브러리 조회');
    }
  }

  /** 헬스 체크 */
  async health() {
    try {
      const { data } = await firstValueFrom(
        this.http.get(`${this.backendUrl}/health`),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, '헬스 체크');
    }
  }

  private handleBackendError(err: unknown, context: string): never {
    if (err instanceof AxiosError) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.message;
      this.logger.error(`${context} 실패 [${status}]: ${detail}`);

      if (status === 400) throw new BadRequestException(detail);
      if (!err.response) throw new ServiceUnavailableException(`백엔드 서비스에 연결할 수 없습니다.`);
      throw new BadGatewayException(`백엔드 오류: ${detail}`);
    }
    throw new BadGatewayException(`${context} 중 알 수 없는 오류가 발생했습니다.`);
  }
}
